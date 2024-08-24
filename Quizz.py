import math
from BodyLandmarkPosition import BodyLandmarkPosition
from config import svc_configs

configs = svc_configs()
default_settings  = configs["default"]["settings"]
offsets_settings = configs["offsets"]["settings"]

quizz_started = False
end_user_quiz = False

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
            return True
        else:
            return False

    def check_hands_up(self):
        left_thumb = self.get_landmark('LEFT_THUMB')
        right_thumb = self.get_landmark('RIGHT_THUMB')
        nose = self.get_landmark('NOSE')

        if not all([left_thumb, right_thumb, nose]):
            return None

        if left_thumb[1] < nose[1] and right_thumb[1] < nose[1]:
            return True
        else:
            return False

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
    

class HandLandmarkPostion:
    def __init__(self, landmarks, handness, mp_hands, cv2, image):
        self.landmarks = landmarks
        self.handness = handness
        self.mp_hands = mp_hands
        self.cv2 = cv2
        self.image = image

    def get_hand_info(self):
        hand_info = []

        if self.handness is None:
            return None
        
        for idx, clf in enumerate(self.handness):
            hand_dict = {
                'label': clf.classification[0].label,
                'idx': idx 
            }
            hand_info.append(hand_dict)

        return hand_info
        
    def landmark_list(self, idx):
        return [(lm.x, lm.y, lm.z) for lm in  self.landmarks[idx].landmark]

    def get_landmark(self, landmark_name, idx):
        landmarks = self.landmark_list(idx)
        landmark = landmarks[self.mp_hands.HandLandmark[landmark_name].value]
        return landmark if 0 <= landmark[0] <= 1 and 0 <= landmark[1] <= 1 else None

    def calculate_position(self, handmark):
        image_height, image_width, _ = self.image.shape

        x = int(handmark[0] * image_width)
        y = int(handmark[1] * image_height)
        z = int(handmark[2] * image_width)

        return (x, y, z)
    

def start_quiz_func(args, args2, trackType, results, currentUser, send_user_message, writter):
    try:
        global quizz_started
        common = GestureCommon(**args)

        hands_up = common.check_hands_up()
        crossed_arm = common.check_crossed_arms()

        if not quizz_started:
            if hands_up is not None:
                if hands_up:
                    quizz_started = hands_up

        if quizz_started:
            end_quizz = False

            if crossed_arm is not None:
                if crossed_arm: 
                    end_quizz = False
                    quizz_started = False

            if not end_quizz:
                hand_landmark = HandLandmarkPostion(**args2)
                hands_info = hand_landmark.get_hand_info()

                organ_quizz = default_settings["organs_quizz"]
                organ_selected = organ_quizz[trackType]

                if hands_info is not None:
                    calc_middle_finger_mcp = []
                    for hand_info in hands_info:
                        middle_finger_mcp = hand_landmark.get_landmark("MIDDLE_FINGER_MCP", hand_info["idx"])
                        # print(hand_info["label"], " => ", hand_landmark.calculate_position(middle_finger_mcp))
                        mcp_dict = { "hand": hand_info["label"], "calc": middle_finger_mcp }
                        calc_middle_finger_mcp.append(mcp_dict)
                    

                    if results is not None:
                        # already handle
                        # if isinstance(results, str) and results == default_settings["err_distance"]:
                        #     print("The person is not at the proper distance. Please move closer or farther to adjust to the correct distance.")
                                
                        if not isinstance(results, str):    
                            common_position, unity_position = results
                            calc_data = []

                            for calc in calc_middle_finger_mcp:
                                res = do_calc_diff(calc["calc"], common_position)
                                calc["result"] = res
                                calc_data.append(calc)      
                            
                            if organ_selected["with_both_hand"]:
                                if len(calc_data) == 2:
                                    print(calc_data)
                            elif not organ_selected["with_both_hand"]:
                                for data in calc_data:
                                    if data["hand"] == organ_selected["which_hand"]:
                                        print(calc_data)
                                    elif organ_selected["which_hand"] == "NONE":
                                        print(calc_data)


    except Exception as e:
        print(e)


def do_calc_diff(calc_mcp, common_position): 
    x = abs(calc_mcp[0]) - abs(common_position[0])
    y = abs(calc_mcp[1]) - abs(common_position[1])

    return (x, y)
