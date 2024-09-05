import cv2
import numpy as np
import mediapipe as mp
import json
import asyncio
import time
import math

from BodyLandmarkPosition import calculate_position, calculate_position_v2
from Quizz import start_quiz_func
from Logger import calc_time_and_log, setup_logger_svc
from config import svc_configs
from datetime import datetime, timezone

# --------------------------------------------------------------------------------------------
svc_logger = setup_logger_svc()

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

# --------------------------------------------------------------------------------------------
#  GLOBALS
# STORE WRITER FOR CLIENT
clients = {}
typeSelected = None
start_time=0
# --------------------------------------------------------------------------------------------

def register_user(userUUID, userRole, addr, writer):
    try:
        checkUser = clients.get(userUUID, None)

        if checkUser:
            if clients[userUUID]['role'] != userRole:
                svc_logger.info(f"user {userUUID} change role from {clients[userUUID]['role']} to {userRole}")
                clients[userUUID]['role'] = userRole

            if clients[userUUID]['port'] != addr[1]:
                svc_logger.info(f"user {userUUID} reconnect from prev port {clients[userUUID]['port']} to {addr}")
                clients[userUUID]['port'] = addr[1]
                clients[userUUID]['writer'] = writer
                

        if checkUser is None:
            clients[userUUID] = {
                'role': userRole,
                'port': addr[1],
                'writer': writer
            }

            svc_logger.info("register user: " + str([userUUID, userRole]))

    except Exception as e:
        svc_logger.info("Error in registering user")


def adjust_orientation(frame):
    # Check if the image is in portrait mode
    if frame.shape[1] > frame.shape[0]:
        frame = cv2.rotate(frame, cv2.ROTATE_90_CLOCKWISE)
    return frame
    # return cv2.rotate(frame, cv2.ROTATE_90_CLOCKWISE)


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
async def receive_json(reader):
    try:
        length_prefix = await reader.readexactly(4)
        if not length_prefix:
            return None, None

        json_length = int.from_bytes(length_prefix, byteorder='little')
        json_data = await reader.readexactly(json_length)
        json_str = json_data.decode('utf-8')
       
        json_msg = json.loads(json_str)

        return json_msg  
    
    except asyncio.IncompleteReadError:
        return None
    except Exception as e:
        return None
    
# Recieve Video FRAME from clients
async def receive_frame(reader):
    try:
        length_prefix = await reader.readexactly(4)
            
        frame_length = int.from_bytes(length_prefix, byteorder='little')
        frame_data = await reader.readexactly(frame_length)

        frame_array = np.frombuffer(frame_data, dtype=np.uint8)
        frame = cv2.imdecode(frame_array, cv2.IMREAD_COLOR)

        return frame
    
    except asyncio.IncompleteReadError:
        return None
    except Exception as e:
        return None

# send UNITY POSITION to HOST
async def send_position(userUUID, unity_position):
    global start_time
    checkUser = clients.get(userUUID, None)

    try:
        if checkUser:
            writer = clients[userUUID]['writer']
            role = clients[userUUID]['role']

            data = json.dumps(unity_position).encode('utf-8')
            length_prefix = len(data).to_bytes(4, byteorder='little')
            writer.write(length_prefix + data)
            
            end_time = time.time()
            calc_time_and_log(topic='send_position', start_time=start_time, end_time=end_time)

            await writer.drain()

    except (ConnectionResetError, BrokenPipeError, OSError) as e:
        # print(f"Error sending json message: {e}. The client might have disconnected.")
        svc_logger.info(f"Error sending json message: {e}. The client might have disconnected.")
        await handle_disconnection(userUUID, role, writer)

    except Exception as e:
        # print(f"Error sending json message: {e}")
        svc_logger.info(f"Error sending json message: {e}")


async def send_json_message(userUUID, json_msg):
    checkUser = clients.get(userUUID, None)

    try:
        if checkUser:
            writer = clients[userUUID]['writer']
            role = clients[userUUID]['role']

            if writer.is_closing():
                return
            
            data = json.dumps(json_msg).encode('utf-8')
            length_prefix = len(data).to_bytes(4, byteorder='little')

            writer.write(length_prefix + data)
            await writer.drain()

    except (ConnectionResetError, BrokenPipeError, OSError) as e:
        # print(f"Error sending json message: {e}. The client might have disconnected.")
        svc_logger.info(f"Error sending json message: {e}. The client might have disconnected.")
        await handle_disconnection(userUUID, role, writer)
    except Exception as e:
        # print(f"Error sending json message: {e}")
        svc_logger.info(f"Error sending json message: {e}")


async def handle_disconnection(userUUID, role, writer):
    try:
        if role and writer and not writer.is_closing():
            writer.close()
            await writer.wait_closed()
            # print(f"Writer for {userUUID} closed.")
            svc_logger.info(f"Writer for [{userUUID}, {role}] closed.")

    except Exception as e:
        # print(f"Error closing writer for {userUUID}: {e}")
        svc_logger.info(f"Error closing writer for {userUUID}: {e}")
    finally:
        if userUUID in clients:
            # print(f"Removing {userUUID} from clients.")
            svc_logger.info(f"Removing [{userUUID}, {role}] from clients.")
            del clients[userUUID]


async def handle_client(reader, writer):
    global start_time
    global typeSelected

    addr = writer.get_extra_info('peername')
    loop = asyncio.get_running_loop()
    is_duplicate_host = False
    position_rotation = None

    try:
        while True:
            start_time = time.time()

            jsonMsg = await receive_json(reader)
            frame = await receive_frame(reader)

            if jsonMsg:
                userUUID = jsonMsg.get('uuid', '')
                userRole = jsonMsg.get('role', '')
                msg_text = jsonMsg.get('message', '')
                position = jsonMsg.get('position', None)
                rotation = jsonMsg.get('rotation', None)
               
                if msg_text == "PING":
                    register_user(userUUID, userRole, addr, writer)
                    # # No Need to send back PONG
                    # pong_msg = { 'message' : "PONG"}
                    # await send_json_message(userUUID, pong_msg)

            count_host = 0
            for client in clients:
                if clients[client]['role'] == "Host":
                    count_host += 1
                    if count_host > 1:
                        is_duplicate_host = True
                        duplicate_host = { 'uuid': client, 'message' : "There are more than one (1) host in this server, please choose only one"}
                        await send_json_message(client, duplicate_host)

            if not is_duplicate_host:
                for client in clients:
                    if clients[client]['role'] == "Host":

                        if frame is None:
                            continue

                        adjustedFrame = frame
                        typeSelected = msg_text

                        if default_settings["adjust_orientation"]:
                            adjustedFrame = adjust_orientation(frame=frame);
                        if default_settings["override_type_selected"]:
                            typeSelected = default_settings["debug_organ"]

                        if isinstance(track_supported, list):
                            if typeSelected in track_supported:

                                results, image = await loop.run_in_executor(None, process_frame, adjustedFrame, typeSelected.lower())
                                if results is not None:    
                                    if isinstance(results, str) and results == default_settings["err_distance"]:
                                        message = "The person is not at the proper distance. Please move closer or farther to adjust to the correct distance."
                                        error_message = { 'uuid': client, 'message' : message}
                                        await send_json_message(client, error_message)
                                    else:
                                        common_position, unity_position = results
                                        await send_position(client, unity_position)

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

                    elif clients[client]['role'] == "Guest":
                        if position_rotation:
                            await send_json_message(client, position_rotation)

            await asyncio.sleep(0.05)
    except Exception as e:
        print(f"Exception in client thread: {e}")
        cv2.destroyWindow(addr[0])
    finally:
        writer.close()
        await writer.wait_closed()
        print(f"Connection to {addr} closed.")


async def cb(reader, writer):
    addr = writer.get_extra_info('peername')
    # print(f'Accepted connection from {addr}')
    svc_logger.info(f'Accepted connection from {addr}')
    await handle_client(reader, writer)

async def unity_stream():
    host = '0.0.0.0'
    port = 5000

    server = await asyncio.start_server(cb, host, port)
    current_time_gmt = datetime.now(timezone.utc)

    svc_msg = f'Server start at {current_time_gmt}, server port: {port}'
    svc_logger.info(svc_msg)

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
    print("Default settings  => ", configs["default"])

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