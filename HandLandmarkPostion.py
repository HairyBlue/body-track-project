import cv2
import mediapipe as mp


mp_drawing = mp.solutions.drawing_utils
mp_drawing_styles = mp.solutions.drawing_styles

mp_hands = mp.solutions.hands
hands = mp_hands.Hands(static_image_mode=False,
                        model_complexity=1,
                        min_detection_confidence=0.5,
                        min_tracking_confidence=0.5)

class HandLandmarkPostion:
   def __init__(self, image, hands_results, hands_marks):
      self.image = image
      self.hands_results = hands_results
      self.hands_marks = hands_marks

   def draw_landmark(self):
      for hand_landmarks in self.hands_marks:
         mp_drawing.draw_landmarks(self.image, hand_landmarks, mp_hands.HAND_CONNECTIONS)

   def landmark_list(self):
      return [(lm.x, lm.y, lm.z) for lm in  self.hands_marks.landmark]

   def get_landmark(self, landmark_name):
      landmarks = self.landmark_list()
      landmark = landmarks[mp_hands.HandLandmark[landmark_name].value]
      return landmark if 0 <= landmark[0] <= 1 and 0 <= landmark[1] <= 1 else None
   


def hand_position(image, hands_results, hands_marks):
   init_hand = HandLandmarkPostion(image, hands_results, hands_marks);
   init_hand.draw_landmark()

      



