import cv2
import mediapipe as mp
from cvzone.PoseModule import PoseDetector

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


def cvzones():
    # Initialize the webcam and set it to the third camera (index 2)
    cap = cv2.VideoCapture(0)
    # cap = cv2.imread("/pose.jpg")

    # Initialize the PoseDetector class with the given parameters
    detector = PoseDetector(staticMode=False,
                            modelComplexity=1,
                            smoothLandmarks=True,
                            enableSegmentation=False,
                            smoothSegmentation=True,
                            detectionCon=0.5,
                            trackCon=0.5)

    # Loop to continuously get frames from the webcam
    while True:
        # Capture each frame from the webcam
        success, img = cap.read()

        # Find the human pose in the frame
        img = detector.findPose(img)

        # Find the landmarks, bounding box, and center of the body in the frame
        # Set draw=True to draw the landmarks and bounding box on the image
        lmList, bboxInfo = detector.findPosition(img, draw=True, bboxWithHands=False)

        # Check if any body landmarks are detected
        if lmList:
            # Get the center of the bounding box around the body
            center = bboxInfo["center"]

            # Draw a circle at the center of the bounding box
            cv2.circle(img, center, 5, (255, 0, 255), cv2.FILLED)

            # Calculate the distance between landmarks 11 and 15 and draw it on the image
            length, img, info = detector.findDistance(lmList[11][0:2],
                                                    lmList[15][0:2],
                                                    img=img,
                                                    color=(255, 0, 0),
                                                    scale=10)

            # Calculate the angle between landmarks 11, 13, and 15 and draw it on the image
            angle, img = detector.findAngle(lmList[11][0:2],
                                            lmList[13][0:2],
                                            lmList[15][0:2],
                                            img=img,
                                            color=(0, 0, 255),
                                            scale=10)

            # Check if the angle is close to 50 degrees with an offset of 10
            isCloseAngle50 = detector.angleCheck(myAngle=angle,
                                                targetAngle=50,
                                                offset=10)

            # Print the result of the angle check
            print(isCloseAngle50)

        # Display the frame in a window
        cv2.imshow("Image", img)

        # Wait for 1 millisecond between each frame
        cv2.waitKey(1)