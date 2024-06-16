import cv2
import socket
import numpy as np
import sys
import mediapipe as mp
from positions import calculateOrganPosition
import json

isUnity = True

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

def receive_frame(conn):
    length_prefix = conn.recv(4)
    if not length_prefix:
        return None
    
    frame_length = int.from_bytes(length_prefix, byteorder='little')
    frame_data = b''
    
    while len(frame_data) < frame_length:
        packet = conn.recv(frame_length - len(frame_data))
        if not packet:
            return None
        frame_data += packet
    
    frame_array = np.frombuffer(frame_data, dtype=np.uint8)
    frame = cv2.imdecode(frame_array, cv2.IMREAD_COLOR)
    
    return frame

def send_position(conn, position):
    try:
        data = json.dumps(position).encode('utf-8')
        print(data)
        length_prefix = len(data).to_bytes(4, byteorder='little')
        conn.sendall(length_prefix + data)
    except Exception as e:
        print(f"Error sending position: {e}")

def process_frame(frame):
    image = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    image.flags.writeable = False
    results = pose.process(image)
    landmarks = results.pose_landmarks
  
    if results.pose_landmarks:
        image.flags.writeable = True
        image = cv2.cvtColor(image, cv2.COLOR_RGB2BGR)
        mp_drawing.draw_landmarks(image, results.pose_landmarks, mp_pose.POSE_CONNECTIONS)

        if landmarks:
            try:
                orgPosition = calculateOrganPosition('heart', landmarks, mp_pose,cv2,image)
                cv2.imshow("Mediapipe feed", image)
                return orgPosition
            except:
                print("error ambot asa")


    
        # if cv2.waitKey(10) & 0xFF == ord('q'):
        #     break    

def adjust_orientation(frame):
    # Check if the image is in portrait mode
    if frame.shape[1] > frame.shape[0]:
        frame = cv2.rotate(frame, cv2.ROTATE_90_CLOCKWISE)
    return frame
    # return cv2.rotate(frame, cv2.ROTATE_90_CLOCKWISE)

def unityCon():
    host = '0.0.0.0'
    port = 5000

    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.bind((host, port))
    server_socket.listen(1)
    
    print('Waiting for a connection...')
    conn, addr = server_socket.accept()
    print('Connected to:', addr)

    try:
        while True:
            frame = receive_frame(conn)
            if frame is None:
                break
            frame = adjust_orientation(frame=frame)

            sendTo = process_frame(frame=frame)

            if sendTo is not None:
                send_position(conn=conn, position=sendTo)
            else:
                print("Palayu uy")
            cv2.waitKey(1)
            if cv2.waitKey(1) & 0xFF == ord('q'):
                break
    except KeyboardInterrupt:
        sys.exit()
    finally:
        conn.close()
        server_socket.close()
        cv2.destroyAllWindows() 
     


def feed():
    cap = cv2.VideoCapture(0)
    # with mp_pose.Pose(static_image_mode=True, model_complexity=1, smoothLandmarks=True, enableSegmentation=False, smoothSegmentation=True ,min_detection_confidence=0.5, min_tracking_confidence=0.5) as pose:
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
                try:
                    calculateOrganPosition('heart', landmarks, mp_pose,cv2,image)
                except:
                    print("error ambot asa")
                    
            cv2.imshow("Mediapipe feed", image)
            cv2.waitKey(1)
            # if cv2.waitKey(10) & 0xFF == ord('q'):
            #     break    
    cap.release()
    cv2.destroyAllWindows()  

def main():
    if isUnity:
        unityCon()
    else:
        feed()
if __name__ == '__main__':
   try: 
    main()
   except TypeError:
    print(TypeError) 