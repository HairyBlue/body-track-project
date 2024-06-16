import cv2
import mediapipe as mp
from positions import OrganPosition

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
                    organ = OrganPosition(landmarks, mp_pose,cv2,image)
                    organ.heartPostion()
                except:
                    print("error ambot asa")
                    
            cv2.imshow("Mediapipe feed", image)
            cv2.waitKey(1)
            # if cv2.waitKey(10) & 0xFF == ord('q'):
            #     break    
    cap.release()
    cv2.destroyAllWindows()   