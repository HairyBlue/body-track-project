import math
from BodyLandmarkPosition import BodyLandmarkPosition, all_organ_position

class GestureCommand(BodyLandmarkPosition):
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

        left_wrist = self.get_landmark('RIGHT_WRIST')
        right_wrist = self.get_landmark('RIGHT_WRIST')

        # if left_wrist is None or right_wrist is None:
        #     return None
        if left_wrist is None:
            return None
        
        left_wrist_x = int(left_wrist[0] * image_width)
        left_wrist_y = int(left_wrist[1] * image_height)

        # right_wrist_x = int(right_wrist[0] * image_width)
        # right_wrist_y = int(right_wrist[1] * image_height)

       
        self.cv2_circle(organ_postion=(left_wrist_x, left_wrist_y ))
        # self.cv2_circle(organ_postion=(right_wrist_x, right_wrist_y ))


        # return (left_wrist_x, left_wrist_y), (right_wrist_x, right_wrist_y)
        return (left_wrist_x, left_wrist_y)

def get_gesture_command(landmarks, mp_pose, cv2, image, trackable):
    command = GestureCommand(landmarks=landmarks, mp_pose=mp_pose, cv2=cv2, image=image)

    if not trackable: 
        return command.check_hands_up(), None
    

    if trackable:
        organs = all_organ_position(landmarks, mp_pose, cv2, image)
        wrist_p =  command.calculate_wrist_position()
        
        for organ_name, organ in organs.items():
            org =  organ.get_position()
            if org is not None and organ_name == 'liver':
                if org is not None and wrist_p is not None:
                    print(int( (wrist_p[1] - org[0][1]) + (wrist_p[0] - org[0][0]) / 2))


        return command.check_crossed_arms(), None
    


    return None, None