import cv2
import numpy as np
import mediapipe as mp
import json
import asyncio

from positions import calculate_organ_position

isUnity = True
organType = 'brain'

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

def process_frame(frame):
    image = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    image.flags.writeable = False
    results = pose.process(image)
    landmarks = results.pose_landmarks
    
    if results.pose_landmarks:
        image.flags.writeable = True
        image = cv2.cvtColor(image, cv2.COLOR_RGB2BGR)
        mp_drawing.draw_landmarks(image, results.pose_landmarks, mp_pose.POSE_CONNECTIONS)

        orgPosition = calculate_organ_position(organType, landmarks, mp_pose,cv2,image)

        return orgPosition, image
    
    return None, None


def adjust_orientation(frame):
    # Check if the image is in portrait mode
    if frame.shape[1] > frame.shape[0]:
        frame = cv2.rotate(frame, cv2.ROTATE_90_CLOCKWISE)
    return frame
    # return cv2.rotate(frame, cv2.ROTATE_90_CLOCKWISE)


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
    
    except asyncio.IncompleteReadError:
        return None

async def send_position(writer, position):
    try:
        data = json.dumps(position).encode('utf-8')
        length_prefix = len(data).to_bytes(4, byteorder='little')
        writer.write(length_prefix + data)
        await writer.drain()

    except Exception as e:
        print(f"Error sending position: {e}")


async def handle_client(reader, writer):
    addr = writer.get_extra_info('peername')
    loop = asyncio.get_running_loop()

    try:
        while True:
            frame = await receive_frame(reader)
            if frame is None:
                break

            # frame = adjust_orientation(frame=frame)
            orgPosition, image = await loop.run_in_executor(None, process_frame, frame)
            
            if orgPosition is not None:               
                await send_position(writer, position=orgPosition)

            if image is None:
                cv2.imshow(addr[0], image)
                cv2.waitKey(1)

            await asyncio.sleep(0.012)

    except Exception as e:
        print(f"Exception in client thread: {e}")
        cv2.destroyWindow(addr[0])
    finally:
        writer.close()
        await writer.wait_closed()
        print(f"Connection to {addr} closed.")


async def cb(reader, writer):
    addr = writer.get_extra_info('peername')
    print(f'Accepted connection from {addr}')
    await handle_client(reader, writer)


async def unity_stream():
    host = '0.0.0.0'
    port = 5000

    server = await asyncio.start_server(cb, host, port)
    print(f'Server listening on {host}:{port}')

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
                calculate_organ_position(organType, landmarks, mp_pose,cv2,image)
      
            cv2.imshow("Mediapipe feed", image)
            cv2.waitKey(1)
 
    cap.release()
    cv2.destroyAllWindows()  

def main():
    if isUnity:
        asyncio.run(unity_stream())
    else:
        debug_feed()

if __name__ == '__main__':
    main()