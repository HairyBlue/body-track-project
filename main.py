import cv2
import numpy as np
import mediapipe as mp
import json
import asyncio
import time
import math
import traceback

from BodyLandmarkPosition import calculate_position_v2
from Quizz import start_quiz_func
from Logger import svc_log, calc_time_and_log
from config import svc_configs
from datetime import datetime, timezone

# --------------------------------------------------------------------------------------------
# # Configs and Setup

configs = svc_configs()
default_settings  = configs["default"]["settings"]
main_runner = default_settings["main_runner"]
track_supported = default_settings["track_supported"]

mp_settings_pose = default_settings["mp"]["pose"]
mp_settings_hands = default_settings["mp"]["hands"]
mp_drawing = mp.solutions.drawing_utils
mp_drawing_styles = mp.solutions.drawing_styles

mp_pose = mp.solutions.pose
pose = mp_pose.Pose(**mp_settings_pose)

mp_hands = mp.solutions.hands
hands = mp_hands.Hands(**mp_settings_hands)

is_cv2_show = default_settings.get("cv2_show", False)
# --------------------------------------------------------------------------------------------
#  GLOBALS

clients = {}
typeSelected = None
start_time = 0
# --------------------------------------------------------------------------------------------

# all staled user must be remove. para gamay nalang ang ehh Loop kahayahay sa nag pa bilin
# More details
# This function removes users who have been inactive for longer than the allowed TTL (time-to-live).
# It checks each user's last active time and disconnects them if the elapsed time exceeds the TTL.
# The `handle_disconnection` function is called to handle the cleanup for inactive users.
async def remove_staled_user():
    p_time = time.time()
    users_ttl = default_settings.get('users_ttl', None)

    if users_ttl:
        if len(clients) > 0:
            for client in clients:
                elapsed_time = p_time - clients[client]['time']
                if elapsed_time > users_ttl:
                    await handle_disconnection(client, clients[client]['role'], clients[client]['writer'])


# For registering and updated changed about the user... igo ragud geh save ug update sa dictionary rag JSON sa javascript
# More details
# This function registers a new user or updates existing user details in the `clients` dictionary.
# It updates the user’s last active time, role, address, port, and writer if they have changed.
# New users are added to the dictionary with their initial details. Logging is used to track changes.
async def register_user(userUUID, userRole, addr, writer):
    checkUser = clients.get(userUUID, None)
    try:
        
        if checkUser:
            clients[userUUID]['time'] = time.time()

            if clients[userUUID]['role'] != userRole:
                svc_log(f"user [{userUUID}, {clients[userUUID]['role']}] change role from {clients[userUUID]['role']} to {userRole}")
                clients[userUUID]['role'] = userRole

            if clients[userUUID]['port'] != addr[1]:
                svc_log(f"user [{userUUID}, {clients[userUUID]['role']}] reconnect from prev port {clients[userUUID]['port']} to {addr}")
                clients[userUUID]['role'] = userRole
                clients[userUUID]['writer'] = writer
                clients[userUUID]['port'] = addr[1]

        if checkUser is None:
            clients[userUUID] = {
                'role': userRole,
                'address': addr[0],
                'port': addr[1],
                'writer': writer,
                'time': time.time()
            }

            svc_log("register user: " + str([userUUID, userRole]))

    except Exception as e:
        svc_log("Error in registering user")
        traceback.print_exc()


# adjust frame/image from landscape to portrait mode
# More details
# This function adjusts the orientation of the provided frame.
# If the frame is in landscape mode (width greater than height), it rotates the frame to portrait mode.
# This ensures the frame is correctly oriented for further processing.
def adjust_orientation(frame):
    if frame.shape[1] > frame.shape[0]:
        frame = cv2.rotate(frame, cv2.ROTATE_90_CLOCKWISE)
    return frame
    # return cv2.rotate(frame, cv2.ROTATE_90_CLOCKWISE)


# this will process the frame and calculate the position based on the organ selected.... ambot ug Strategy pattern ang geh follow sa pag calc.
# More details
# This function processes a video frame to calculate positions based on organ landmarks.
# It converts the frame to RGB, processes it with pose and hand models, and calculates positions based on landmarks.
# The processed frame is returned along with the calculated position results.
def process_frame(frame, trackType):
    results = None
    image = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    image.flags.writeable = False

    if default_settings["image_flip"]:
        image = cv2.flip(image, 1);
    
    # mp_pose
    pose_results = pose.process(image)
    landmarks = pose_results.pose_landmarks

    # mp_hands
    hands_results = hands.process(image)
    hands_marks = hands_results.multi_hand_landmarks
    handness = hands_results.multi_handedness

    if landmarks or hands_marks:
        image.flags.writeable = True
        image = cv2.cvtColor(image, cv2.COLOR_RGB2BGR)

        if hands_marks:
            for hand_landmarks in hands_marks:
                mp_drawing.draw_landmarks(image, hand_landmarks, mp_hands.HAND_CONNECTIONS)

        if landmarks:
            args = {
                'landmarks': landmarks,
                'mp_pose': mp_pose,
                'cv2': cv2,
                'image': image
            }

            args2 = {
                'landmarks': hands_marks,
                'handness': handness,
                'mp_hands': mp_hands,
                'cv2': cv2,
                'image': image
            }

            mp_drawing.draw_landmarks(image, landmarks, mp_pose.POSE_CONNECTIONS)
            results =  calculate_position_v2(trackType, args)

            # if startQuiz:
            #     start_quiz_func(args, args2, trackType, results, currentUser, send_user_message, writer)
        
    return results, image

# Recieve JSON from clients
# More details
# This function receives and decodes a JSON message from the client.
# It reads the length prefix to determine the size of the JSON data, then reads and decodes the JSON message.
# It handles incomplete reads and other exceptions gracefully, returning `None` if an error occurs.
async def receive_json(reader):
    try:
        length_prefix = await reader.readexactly(4)
        if not length_prefix:
            return None

        json_length = int.from_bytes(length_prefix, byteorder='little')
        json_data = await reader.readexactly(json_length)
        json_str = json_data.decode('utf-8')
       
        json_msg = json.loads(json_str)

        return json_msg  
    
    except asyncio.IncompleteReadError as e:
        return None
    except UnicodeDecodeError as e:
        return None
    except json.JSONDecodeError as e:
        return None
    except Exception as e:
        return None
    

# Recieve Video FRAME from clients
# More details
# This function receives and decodes a video frame from the client.
# It reads the length prefix to determine the size of the frame data, then reads and decodes the frame.
# It handles incomplete reads and other exceptions gracefully, returning `None` if an error occurs.
async def receive_frame(reader):
    try:
        length_prefix = await reader.readexactly(4)

        if not length_prefix:
            return None
        
        frame_length = int.from_bytes(length_prefix, byteorder='little')
        frame_data = await reader.readexactly(frame_length)

        frame_array = np.frombuffer(frame_data, dtype=np.uint8)
        frame = cv2.imdecode(frame_array, cv2.IMREAD_COLOR)

        return frame
    
    except asyncio.IncompleteReadError as e:
        return None
    except cv2.error as e:
        return None
    except Exception as e:
        return None


# send UNITY POSITION to HOST
# More details
# This function sends the calculated unity position to a specified user.
# It encodes the position data in JSON format and sends it to the user using their writer.
# It handles connection errors and ensures the writer is closed properly if there are issues.
async def send_unity_position(userUUID, unity_position):
    global start_time
    checkUser = clients.get(userUUID, None)

    try:
        if checkUser:
            writer = clients[userUUID]['writer']
            user_role = clients[userUUID]['role']

            data = json.dumps(unity_position).encode('utf-8')
            length_prefix = len(data).to_bytes(4, byteorder='little')
            writer.write(length_prefix + data)
            
            await writer.drain()

            end_time = time.time()
            calc_time_and_log(topic='send_unity_position', role=user_role, start_time=start_time, end_time=end_time)

    except (ConnectionResetError, BrokenPipeError, OSError) as e:
        svc_log(f"Error sending json message: {e}. The client might have disconnected.", "ERROR")
        await handle_disconnection(userUUID, user_role, writer)

    except Exception as e:
        svc_log(f"Error sending json message: {e}", "ERROR")


# This function sends a JSON message to a specified user.
# It encodes the message in JSON format and sends it using the user's writer.
# It handles connection errors and ensures the writer is closed properly if there are issues.
async def send_json_message(userUUID, json_msg):
    global start_time
    checkUser = clients.get(userUUID, None)

    try:
        if checkUser:
            writer = clients[userUUID]['writer']
            user_role = clients[userUUID]['role']

            if writer.is_closing():
                return
            
            data = json.dumps(json_msg).encode('utf-8')
            length_prefix = len(data).to_bytes(4, byteorder='little')

            writer.write(length_prefix + data)
            await writer.drain()

            end_time = time.time()
            calc_time_and_log(topic='send_json_message', role=user_role, start_time=start_time, end_time=end_time)

    except (ConnectionResetError, BrokenPipeError, OSError) as e:
        svc_log(f"Error sending json message: {e}. The client might have disconnected.", "ERROR")
        await handle_disconnection(userUUID, user_role, writer)
    except Exception as e:
        svc_log(f"Error sending json message: {e}", "ERROR")


# This function handles user disconnections.
# It closes the writer for the specified user and removes the user from the `clients` dictionary.
# Logging is used to track the closure and removal of users.
async def handle_disconnection(userUUID, role, writer):
    try:
        if role and writer and not writer.is_closing():
            writer.close()
            await writer.wait_closed()
            svc_log(f"Writer for [{userUUID}, {role}] closed.")

        if userUUID in clients:
            del clients[userUUID]
            svc_log(f"Removing [{userUUID}, {role}] from clients. Current number of clients connected ({len(clients)})")

    except Exception as e:
        svc_log(f"Error closing writer for {userUUID}: {e}", "ERROR")
    finally:
        # Ensure it removes
        if userUUID in clients:
            del clients[userUUID]
            svc_log(f"Ensure to remove [{userUUID}, {role}] from clients. Current number of clients connected ({len(clients)})", "WARN")


# maintain client connection and process them... wanakoy masulti kay naana dinhia tanang publema
# More details
# This function maintains client connections and processes incoming data.
# It handles JSON and frame data, manages user roles, and ensures only one host is active.
# It processes frames to calculate positions, updates clients with new information, and manages client disconnections.
async def handle_client(reader, writer):
    global start_time
    global typeSelected

    addr = writer.get_extra_info('peername')
    loop = asyncio.get_running_loop()
    position_rotation = None
    cachedFrame = None
    not_empty_mult_host = False

    try:
        while True:
            start_time = time.time()
            
            if reader.at_eof():
                svc_log("Reader reached EOF. Possible Host disconnect or quit")
                break

            jsonMsg = await receive_json(reader)
            frame = await receive_frame(reader)

            if jsonMsg:
                userUUID = jsonMsg.get('uuid', None)
                userRole = jsonMsg.get('role', None)
                msg_text = jsonMsg.get('message', None)
                position = jsonMsg.get('position', None)
                rotation = jsonMsg.get('rotation', None)
               
                if msg_text == "PING":
                    # if userUUID and userRole and msg_text:
                    await register_user(userUUID, userRole, addr, writer)
                    # # No Need to send back PONG
                    # pong_msg = { 'message' : "PONG"}
                    # await send_json_message(userUUID, pong_msg)

            # remove user that no longer active... kung sa DULA pah AFK nah. inang dayug easy farm.
            await remove_staled_user()       
            
            # count if how many host in the clients list... kay mabuang ang ning server kung duha
            count_host = sum(1 for client in clients if clients[client]['role'] == "Host")
            if count_host > 1:
                not_empty_mult_host = True
            
            # Notify all hosts about the issue of multiple hosts connection.... para nice feature kunuhay
            if not_empty_mult_host: 
                for client in clients:
                    if clients[client]['role'] == "Host":
                        duplicate_host_msg = { 'uuid': client, 'message': "There are multiple hosts. Only one is allowed." }
                        await send_json_message(client, duplicate_host_msg)
                

            if count_host == 1:
                if not_empty_mult_host:
                    for client in clients:
                        duplicate_host_msg = { 'uuid': client, 'message': "" }
                        await send_json_message(client, duplicate_host_msg)

                    not_empty_mult_host = False

                if frame is not None:
                    cachedFrame = frame
                    host_client = next(client for client in clients if clients[client]['role'] == "Host")
                
                    adjustedFrame = frame
                    if msg_text is not None:
                        typeSelected = msg_text

                    if default_settings["adjust_orientation"]:
                        adjustedFrame = adjust_orientation(frame=cachedFrame)
                    if default_settings["override_type_selected"]:
                        typeSelected = default_settings["debug_organ"]

                    if typeSelected and isinstance(track_supported, list) and typeSelected in track_supported:
                        results, image = await loop.run_in_executor(None, process_frame, adjustedFrame, typeSelected.lower())
                        
                        if results:
                            if isinstance(results, str) and results == default_settings["err_distance"]:
                                error_message = { 'uuid': host_client, 'message': "Adjust your distance from the camera." }
                                await send_json_message(host_client, error_message)
                            else:
                                common_position, unity_position = results
                                await send_unity_position(host_client, unity_position)

                        if is_cv2_show:
                            if image is not None:
                                cv2.imshow(addr[0], image)
                                cv2.waitKey(1)

                    if position and rotation:
                        position_rotation = {
                            "positionX": position['x'],
                            "positionY": position['y'],
                            "positionZ": position['z'],
                            "rotationX": rotation['x'],
                            "rotationY": rotation['y'],
                            "rotationZ": rotation['z']
                        }

                    if position_rotation:
                        for client in clients:
                            if clients[client]['role'] == "Guest" and position_rotation:
                                await send_json_message(client, position_rotation)

            await asyncio.sleep(0.03)
    except Exception as e:
        svc_log(f"Exception in client thread: {e}", "ERROR")
    finally:
        if writer:
            writer.close()
            await writer.wait_closed()
        if addr and addr[0]:
            if is_cv2_show:
                cv2.destroyWindow(addr[0])
        svc_log(f"Connection to {addr} closed. Current number of clients connected {len(clients)}")

# This function handles incoming client connections.
# It retrieves the client's address information from the writer and logs the connection.
# It then calls the `handle_client` function to manage communication with the client.
async def cb(reader, writer):
    addr = writer.get_extra_info('peername')
    svc_log(f'Accepted connection from {addr}')
    await handle_client(reader, writer)


# This function initializes and starts the Unity streaming server.
# It sets the server to listen on all available interfaces at port 5000.
# It logs the server start time and port, then enters a loop to continuously serve incoming client connections.
async def unity_stream():
    host = '0.0.0.0'
    port = 10000 #5000

    server = await asyncio.start_server(cb, host, port)
    current_time_gmt = datetime.now(timezone.utc)

    svc_msg = f'Server start at {current_time_gmt}, server port: {port}'
    svc_log(svc_msg)

    async with server:
        await server.serve_forever()


## ------DEBUGGING SECTION---------------------DEBUGGING SECTION-----------------------DEBUGGING SECTION---------------------------- DEBUGGING SECTION ---------------------DEBUGGING SECTION------------------DEBUGGING SECTION----------------------------------------------------------------------------
def debug_feed():
    cap = cv2.VideoCapture(0)
    while cap.isOpened():
        try:
            start_time = time.time()

            ret, frame = cap.read()

            adjustedFrame = frame

            if default_settings["adjust_orientation"]:
                adjustedFrame = adjust_orientation(frame=frame);
            
            image = cv2.cvtColor(adjustedFrame, cv2.COLOR_BGR2RGB)
            image.flags.writeable = False
            
            if default_settings["image_flip"]:
                image = cv2.flip(image, 1);
            
            pose_results = pose.process(image)
            landmarks = pose_results.pose_landmarks
            
            hands_results = hands.process(image)
            hands_marks = hands_results.multi_hand_landmarks

            if landmarks or hands_marks:
                image.flags.writeable = True
                image = cv2.cvtColor(image, cv2.COLOR_RGB2BGR)

                if hands_marks:
                    for hand_landmarks in hands_marks:
                        mp_drawing.draw_landmarks(image, hand_landmarks, mp_hands.HAND_CONNECTIONS)


                if landmarks:
                    mp_drawing.draw_landmarks(image, landmarks, mp_pose.POSE_CONNECTIONS)
                    
                    # unpack dictionary later
                    args = {
                        'landmarks': landmarks,
                        'mp_pose': mp_pose,
                        'cv2': cv2,
                        'image': image
                    }
                    
                    debug_organ = default_settings["debug_organ"]
                    results =  calculate_position_v2(debug_organ, args)
                    
                    if results is not None:
                        if isinstance(results, str) and results == default_settings["err_distance"]:
                            print("The person is not at the proper distance. Please move closer or farther to adjust to the correct distance.")
                        else:    
                            common_position, unity_position = results

                        end_time = time.time()
                        calc_time_and_log(topic='debug_unity_position', start_time=start_time, end_time=end_time)


                cv2.imshow("Mediapipe feed", image)
                cv2.waitKey(1)
        except Exception as e:
            print(e)

    cap.release()
    cv2.destroyAllWindows()  


def debug_quizz():
    cap = cv2.VideoCapture(0)
    while cap.isOpened():
        ret, frame = cap.read()

        adjustedFrame = frame

        if default_settings["adjust_orientation"]:
            adjustedFrame = adjust_orientation(frame=frame);
        
        image = cv2.cvtColor(adjustedFrame, cv2.COLOR_BGR2RGB)
        
        if default_settings["image_flip"]:
            image = cv2.flip(image, 1);

        image.flags.writeable = False
        
        pose_results = pose.process(image)
        landmarks = pose_results.pose_landmarks
        
        hands_results = hands.process(image)
        hands_marks = hands_results.multi_hand_landmarks
        handness = hands_results.multi_handedness

        if landmarks:
            image.flags.writeable = True
            image = cv2.cvtColor(image, cv2.COLOR_RGB2BGR)
        
            mp_drawing.draw_landmarks(image, landmarks, mp_pose.POSE_CONNECTIONS)

        if hands_marks:
            for hand_landmarks in hands_marks:
                mp_drawing.draw_landmarks(image, hand_landmarks, mp_hands.HAND_CONNECTIONS)
    
            # unpack dictionary later
            args = {
                'landmarks': landmarks,
                'mp_pose': mp_pose,
                'cv2': cv2,
                'image': image
            }

            args2 = {
                'landmarks': hands_marks,
                'handness': handness,
                'mp_hands': mp_hands,
                'cv2': cv2,
                'image': image
            }

            start_quiz_func(args=args, args2=args2)

            cv2.imshow("Mediapipe feed", image)
            cv2.waitKey(1)
 
    cap.release()
    cv2.destroyAllWindows()  

def main():
    log_config = configs["default"]
    svc_log(f"Default settings  =>  {log_config}")

    if main_runner == "unity":
        asyncio.run(unity_stream())
    elif main_runner == "debug":
        debug_feed()
    elif main_runner == "debug_quizz":
        debug_quizz()
    else:
        print("No main runner choosen. Please choose between [unity, debug, debug_quizz] and change the mainRunner on ./settings/default.settings.yaml")
    

if __name__ == '__main__':
    main()