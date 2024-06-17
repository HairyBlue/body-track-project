import cv2
import mediapipe as mp
from BodyLandmarkPosition import OrganPosition

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

def readimg():
    while True:
        img_path = 'pose.jpg'
        image = cv2.imread(img_path)
        image_rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)

        results = pose.process(image_rgb)
        landmarks = results.pose_landmarks
        
        if landmarks:
            try:
                organ = OrganPosition(landmarks, mp_pose,cv2,image)
                organ.heartPostion()
            except:
                print("error ambot asa")

        if results.pose_landmarks:
            mp_drawing.draw_landmarks(image, results.pose_landmarks, mp_pose.POSE_CONNECTIONS)

            cv2.imshow('Pose Landmarks', image)
            cv2.waitKey(2)

    

    # cv2.destroyAllWindows()

    # cv2.imwrite('pose_landmarks_output.jpg', image)