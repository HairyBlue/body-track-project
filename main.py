import cv2
import numpy as np
import mediapipe as mp
import json
import asyncio

from BodyLandmarkPosition import calculate_position
from GestureCommand import get_gesture_command

# for command
trackable = False
isUnity = True
isDebug = False
isCommand = False

mp_drawing = mp.solutions.drawing_utils
mp_drawing_styles = mp.solutions.drawing_styles
mp_pose = mp.solutions.pose
pose = mp_pose.Pose(static_image_mode=False,
                    model_complexity=1,
                    smooth_landmarks=True,
                    enable_segmentation=False,
                    smooth_segmentation=True,
                    min_detection_confidence=0.5,
                    min_tracking_confidence=0.5)

currentUser = ""
typeSelected = ""

user_queue = []
unique_users = set()

supported = [
        'heart',
        'brain',
        'liver',
        'stomach',
        'intestine',
]




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
            print(currentUser)

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
    results = pose.process(image)
    landmarks = results.pose_landmarks
    
    if results.pose_landmarks:
        image.flags.writeable = True
        image = cv2.cvtColor(image, cv2.COLOR_RGB2BGR)
        mp_drawing.draw_landmarks(image, results.pose_landmarks, mp_pose.POSE_CONNECTIONS)

        calcPosition = calculate_position(trackType, landmarks, mp_pose,cv2,image)

        return calcPosition, image
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
    try:
        data = json.dumps(position).encode('utf-8')
        length_prefix = len(data).to_bytes(4, byteorder='little')
        writer.write(length_prefix + data)
        await writer.drain()

    except Exception as e:
        print(f"Error sending position: {e}")

async def send_queue_msg(writer, connectedUser):
    try:
        queueNum =  user_queue.index(connectedUser) + 1
        message = f"There is still user using the body tracking. Your queue number is {queueNum} from {len(user_queue)} number of user/s. Please wait on your turn..."
        queueMsq = {'uuid': connectedUser, 'queue': message}
        print(queueMsq)
        data = json.dumps(queueMsq).encode('utf-8')
        length_prefix = len(data).to_bytes(4, byteorder='little')

        writer.write(length_prefix + data)
        await writer.drain()

    except Exception as e:
        print(f"Error sending queue message: {e}")


async def handle_client(reader, writer):
    global isTrackable
    addr = writer.get_extra_info('peername')
    loop = asyncio.get_running_loop()
    connectedUser = ""

    try:
        while True:
            json_type, jsonMsg = await receive_json(reader)
            frame = await receive_frame(reader)

            
            if jsonMsg and json_type == 'json':
                connectedUser = jsonMsg.get('uuid', '')
                msg_text = jsonMsg.get('message', '')
                register_user(connectedUser, msg_text)
                
            if frame is None:
                break

            if currentUser == user_queue[0]:
                position, image = await loop.run_in_executor(None, process_frame, frame, typeSelected.lower())

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
        ret, frame = cap.read()
        image = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        image.flags.writeable = False
        results = pose.process(image)
        landmarks = results.pose_landmarks

        if results.pose_landmarks:
            image.flags.writeable = True
            image = cv2.cvtColor(image, cv2.COLOR_RGB2BGR)
            mp_drawing.draw_landmarks(image, results.pose_landmarks, mp_pose.POSE_CONNECTIONS)

            if landmarks:
                calculate_position("heart", landmarks, mp_pose,cv2,image)
            
            cv2.imshow("Mediapipe feed", image)
            cv2.waitKey(1)
 
    cap.release()
    cv2.destroyAllWindows()  


def command():
    cap = cv2.VideoCapture(0)
    while cap.isOpened():
        ret, frame = cap.read()
        image = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        image.flags.writeable = False
        results = pose.process(image)
        landmarks = results.pose_landmarks

        if results.pose_landmarks:
            global trackable

            image.flags.writeable = True
            image = cv2.cvtColor(image, cv2.COLOR_RGB2BGR)
            mp_drawing.draw_landmarks(image, results.pose_landmarks, mp_pose.POSE_CONNECTIONS)

            isTracked, switchOrgan =  get_gesture_command(landmarks, mp_pose, cv2,image, trackable)
            
            if isTracked is not None and not trackable:
                trackable = isTracked

            if isTracked is not None and trackable:
                trackable = isTracked
                cv2.destroyAllWindows()

            if trackable:
                if landmarks:
                    
                    cv2.imshow("Mediapipe feed", image)
                    cv2.waitKey(1)
 
    cap.release()
    cv2.destroyAllWindows()  

def main():
    if isUnity:
        asyncio.run(unity_stream())
    if isDebug:
        debug_feed()
    if isCommand:
        command()

if __name__ == '__main__':
    main()





                # if isTrackable:
                
                #     #  topic the message recieve organ or system
                #     # logger start time for frame ms recieve
                #     frame = await receive_frame(reader)
                #     if frame is None:
                #         break
                #     # logger end time for frame ms receive and log it

                #     # frame = adjust_orientation(frame=frame)
                #     # logger start time for frame ms recieve
                #     position, image = await loop.run_in_executor(None, process_frame, frame, "heart")

                #     if position is not None:               
                #         await send_position(writer, position=position)
                #     if image is None:
                #         cv2.imshow(addr[0], image)
                #         cv2.waitKey(1)
