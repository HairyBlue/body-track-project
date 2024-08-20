import math
from BodyLandmarkPosition import BodyLandmarkPosition, calculate_position_v2

quizzStarted = False
organs = ['heart', 'brain', 'liver', 'stomach', 'intestine']

class GestureCommon(BodyLandmarkPosition):
    def __init__(self, landmarks, mp_pose, cv2, image):
        super().__init__(landmarks, mp_pose, cv2, image)

    def slope(self, point1, point2):
        if point1 and point2 and (point2[0] - point1[0]) != 0:
            return (point2[1] - point1[1]) / (point2[0] - point1[0])
        return None
    
    def check_crossed_arms(self):
        left_elbow = self.get_landmark('LEFT_ELBOW')
        right_elbow = self.get_landmark('RIGHT_ELBOW')
        left_wrist = self.get_landmark('LEFT_WRIST')
        right_wrist = self.get_landmark('RIGHT_WRIST')
        nose = self.get_landmark('NOSE')

        # A_x = right_wrist[0] - left_elbow[0]
        # A_y = right_wrist[1] - left_elbow[1]

        # B_x = left_wrist[0] - right_elbow[0]
        # B_y = left_wrist[1] - right_elbow[1]

        #  cross_product = (A_x * B_y) - (A_y * B_x)

        if not all([left_elbow, right_elbow, left_wrist, right_wrist, nose]):
            return None
        
        center_x = nose[0]
        wrists_cross = (left_wrist[0] < center_x and right_wrist[0] > center_x)

        slope_elbow_wrist_l = self.slope(left_elbow, right_wrist)
        slope_elbow_wrist_r = self.slope(right_elbow, left_wrist)

        calc = abs(slope_elbow_wrist_l) + abs(slope_elbow_wrist_r)

        if math.floor(calc) >= 20 and wrists_cross:
            return False

    def check_hands_up(self):
        left_thumb = self.get_landmark('LEFT_THUMB')
        right_thumb = self.get_landmark('RIGHT_THUMB')
        nose = self.get_landmark('NOSE')

        if not all([left_thumb, right_thumb, nose]):
            return None

        if left_thumb[1] < nose[1] and right_thumb[1] < nose[1]:
            return True

    def calculate_wrist_position(self):
        image_height, image_width, _ = self.image.shape

        left_wrist = self.get_landmark('LEFT_WRIST')
        right_wrist = self.get_landmark('RIGHT_WRIST')

        calc_wrist = None, None

        if left_wrist is not None and right_wrist is not None:
            left_wrist_x = int(left_wrist[0] * image_width)
            left_wrist_y = int(left_wrist[1] * image_height)

            right_wrist_x = int(right_wrist[0] * image_width)
            right_wrist_y = int(right_wrist[1] * image_height)

            self.cv2_circle(organ_postion=(left_wrist_x, left_wrist_y ))
            self.cv2_circle(organ_postion=(right_wrist_x, right_wrist_y ))

            calc_wrist = (left_wrist_x, left_wrist_y), (right_wrist_x, right_wrist_y)
        elif left_wrist is not None:
            left_wrist_x = int(left_wrist[0] * image_width)
            left_wrist_y = int(left_wrist[1] * image_height)

            self.cv2_circle(organ_postion=(left_wrist_x, left_wrist_y ))

            calc_wrist = (left_wrist_x, left_wrist_y), None
        
        elif right_wrist is not None:
            right_wrist_x = int(right_wrist[0] * image_width)
            right_wrist_y = int(right_wrist[1] * image_height)

            self.cv2_circle(organ_postion=(right_wrist_x, right_wrist_y ))

            calc_wrist = None, (right_wrist_x, right_wrist_y)
        
        return calc_wrist
    

    def calculate_chosen_organ(self, organ_name , organ_position, hand_position):
        print(organ_name, organ_position, hand_position)


class HandLandmarkPostion:
    def __init__(self, landmarks, mp_hands, cv2, image):
        self.landmarks = landmarks
        self.mp_hands = mp_hands
        self.cv2 = cv2
        self.image = image

    def landmark_list(self):
        return [(lm.x, lm.y, lm.z) for lm in  self.hands_marks.landmark]

    def get_landmark(self, landmark_name):
        landmarks = self.landmark_list()
        landmark = landmarks[self.mp_hands.HandLandmark[landmark_name].value]
        return landmark if 0 <= landmark[0] <= 1 and 0 <= landmark[1] <= 1 else None
    


def start_quiz(args, args2):
    global quizzStarted
    common = GestureCommon(**args)

    hands_up = common.check_hands_up()
    crossed_arm = common.check_crossed_arms()

    if quizzStarted == True:
        if crossed_arm is not None:
            quizzStarted = crossed_arm

    if quizzStarted == False:
        if hands_up is not None:
            quizzStarted = hands_up

    if quizzStarted:
        HandLandmarkPostion(**args2)

        for organ in organs:
            results = calculate_position_v2(organ, args)
            if results is not None:
                common_position, unity_position = results
                common.calculate_chosen_organ(organ, common_position, None)
