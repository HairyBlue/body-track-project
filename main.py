import cv2
import numpy as np
import mediapipe as mp
import json
import asyncio
import time

from BodyLandmarkPosition import calculate_position, calculate_position_v2
from Quizz import start_quiz
from Logger import calc_time_and_log
from config import svc_configs

configs = svc_configs()
default_settings  = configs["default"]["settings"]
main_runner = default_settings["mainRunner"]


mp_settings_pose = default_settings["mp"]["pose"]
mp_settings_hands = default_settings["mp"]["hands"]
mp_drawing = mp.solutions.drawing_utils
mp_drawing_styles = mp.solutions.drawing_styles

mp_pose = mp.solutions.pose
pose = mp_pose.Pose(**mp_settings_pose)

mp_hands = mp.solutions.hands
hands = mp_hands.Hands(**mp_settings_hands)


currentUser = ""
typeSelected = ""

user_queue = []
unique_users = set()

start_time=0

def pop_user(connectedUser):
    if user_queue:
        idx = user_queue.index(connectedUser)
        user = user_queue.pop(idx)
        unique_users.remove(user)
        print(f"User '{user}' removed from unforseen situation. Queue: {user_queue}")
        return user
    print("Queue is empty.")
    return None

def dequeue_user():
    if user_queue:
        user = user_queue.pop(0)
        unique_users.remove(user)
        print(f"User '{user}' removed from the queue. Queue: {user_queue}")
        return user
    print("Queue is empty.")
    return None


def register_user(user, msg):
    global currentUser
    global typeSelected
    try:
        if user and user not in unique_users:
            user_queue.append(user)
            unique_users.add(user)
        
        if user_queue.index(user) == 0:
            currentUser = user  
            typeSelected = msg
            # print(currentUser)

    except Exception as e:
        print("Error in registering user")

def adjust_orientation(frame):
    # Check if the image is in portrait mode
    if frame.shape[1] > frame.shape[0]:
        frame = cv2.rotate(frame, cv2.ROTATE_90_CLOCKWISE)
    return frame
    # return cv2.rotate(frame, cv2.ROTATE_90_CLOCKWISE)


def process_frame(frame, trackType):
    image = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    image.flags.writeable = False

    # mp_pose
    pose_results = pose.process(image)
    landmarks = pose_results.pose_landmarks

    # mp_hands
    hands_results = hands.process(image)
    hands_marks = hands_results.multi_hand_landmarks

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
                'mp_hands': mp_hands,
                'cv2': cv2,
                'image': image
            }

            mp_drawing.draw_landmarks(image, landmarks, mp_pose.POSE_CONNECTIONS)

            command_position, unity_position =  calculate_position_v2(trackType, args)

        if unity_position is not None:
            return unity_position, image
        
    return None, None

async def receive_json(reader):

    try:
        length_prefix = await reader.readexactly(4)
        if not length_prefix:
            return None, None

        json_length = int.from_bytes(length_prefix, byteorder='little')
        json_data = await reader.readexactly(json_length)
        json_str = json_data.decode('utf-8')
       
        json_msg = json.loads(json_str)
        data_type = 'json'
        return data_type, json_msg  
    except asyncio.IncompleteReadError:
        return None, None


async def receive_frame(reader):
    try:
        length_prefix = await reader.readexactly(4)
            
        frame_length = int.from_bytes(length_prefix, byteorder='little')
        frame_data = await reader.readexactly(frame_length)

        frame_array = np.frombuffer(frame_data, dtype=np.uint8)
        frame = cv2.imdecode(frame_array, cv2.IMREAD_COLOR)
        return frame
    
    except asyncio.IncompleteReadError:
        return None, None


async def send_position(writer, position):
    global start_time

    try:
        data = json.dumps(position).encode('utf-8')
        length_prefix = len(data).to_bytes(4, byteorder='little')
        writer.write(length_prefix + data)
        
        end_time = time.time()
        calc_time_and_log(topic='send_position', start_time=start_time, end_time=end_time)

        await writer.drain()
    except Exception as e:
        print(f"Error sending position: {e}")

async def send_queue_msg(writer, connectedUser):
    try:
        queueNum =  user_queue.index(connectedUser) + 1
        message = f"There is still user using the body tracking. Your queue number is {queueNum} from {len(user_queue)} number of user/s. Please wait on your turn..."
        queueMsq = {'uuid': connectedUser, 'queue': message}

        data = json.dumps(queueMsq).encode('utf-8')
        length_prefix = len(data).to_bytes(4, byteorder='little')

        writer.write(length_prefix + data)
        await writer.drain()

    except Exception as e:
        print(f"Error sending queue message: {e}")


async def handle_client(reader, writer):
    global isTrackable
    global start_time

    addr = writer.get_extra_info('peername')
    loop = asyncio.get_running_loop()
    connectedUser = ""

    try:
        while True:
            start_time = time.time()

            json_type, jsonMsg = await receive_json(reader)
            frame = await receive_frame(reader)

            if jsonMsg and json_type == 'json':
                connectedUser = jsonMsg.get('uuid', '')
                msg_text = jsonMsg.get('message', '')
                register_user(connectedUser, msg_text)
                
            if frame is None:
                break

            adjustedFrame = adjust_orientation(frame=frame);

            if currentUser == user_queue[0]:
                position, image = await loop.run_in_executor(None, process_frame, adjustedFrame, typeSelected.lower())
                if position is not None:            
                    await send_position(writer, position=position)

                if image is not None:
                    cv2.imshow(addr[0], image)
                    cv2.waitKey(1)
            else:
                if len(connectedUser) > 0:
                    await send_queue_msg(writer, connectedUser)


            await asyncio.sleep(0.012)
    except Exception as e:
        print(f"Exception in client thread: {e}")
        cv2.destroyWindow(addr[0])
    finally:
        writer.close()
        await writer.wait_closed()
        print(f"Connection to {addr} closed.")
        # dequeue current user
        if currentUser == user_queue[0]:
            dequeue_user()
        # if other user quit or any error happen pop them, dont remove the current user
        pop_user(connectedUser)

async def cb(reader, writer):
    addr = writer.get_extra_info('peername')
    print(f'Accepted connection from {addr}')
    await handle_client(reader, writer)


async def unity_stream():
    host = '0.0.0.0'
    port = 5000

    server = await asyncio.start_server(cb, host, port)
    print(f'Server listening on {host}:{port}')

    # user_queue.append('huy')
    # unique_users.add('huy')

    async with server:
        await server.serve_forever()

def debug_feed():
    cap = cv2.VideoCapture(0)
    while cap.isOpened():
        start_time = time.time()

        ret, frame = cap.read()
        image = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        image.flags.writeable = False

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

                command_position, unity_position =  calculate_position_v2("heart", args)

                if unity_position is not None:
                    end_time = time.time()
                    calc_time_and_log(topic='debug_unity_position', start_time=start_time, end_time=end_time)


            cv2.imshow("Mediapipe feed", image)
            cv2.waitKey(1)

    cap.release()
    cv2.destroyAllWindows()  


def debug_quizz():
    cap = cv2.VideoCapture(0)
    while cap.isOpened():
        ret, frame = cap.read()
        image = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        image.flags.writeable = False
        
        pose_results = pose.process(image)
        landmarks = pose_results.pose_landmarks
        
        hands_results = hands.process(image)
        hands_marks = hands_results.multi_hand_landmarks

        if landmarks:
            image.flags.writeable = True
            image = cv2.cvtColor(image, cv2.COLOR_RGB2BGR)
        
            mp_drawing.draw_landmarks(image, landmarks, mp_pose.POSE_CONNECTIONS)
    
            # unpack dictionary later
            args = {
                'landmarks': landmarks,
                'mp_pose': mp_pose,
                'cv2': cv2,
                'image': image
            }

            args2 = {
                'landmarks': hands_marks,
                'mp_hands': mp_hands,
                'cv2': cv2,
                'image': image
            }

            start_quiz(args=args, args2=args2)

            cv2.imshow("Mediapipe feed", image)
            cv2.waitKey(1)
 
    cap.release()
    cv2.destroyAllWindows()  

def main():
    # unity, debug, debug_quizz
    # main_runner = "unity"

    if main_runner == "unity":
        asyncio.run(unity_stream())
    elif main_runner == "debug":
        debug_feed()
    elif main_runner == "debug_quzz":
        debug_quizz
    else:
        print("No main runner choosen. Please choose between [unity, debug, debug_quizz] and change the mainRunner on ./settings/default.settings.yaml")
    

if __name__ == '__main__':
    main()