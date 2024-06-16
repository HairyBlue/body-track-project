class BodyLandmarkPosition:
    def __init__(self, landmarks, mp_pose, cv2, image):
        self.landmarks = landmarks
        self.mp_pose = mp_pose
        self.cv2 = cv2
        self.image = image

    def cv2_circle(self, color=(0, 0, 255), organ_postion=None):
        if organ_postion is not None:
            # image_height, image_width, _ = self.image.shape
            self.cv2.circle(self.image, (organ_postion[0], organ_postion[1]), 10, color, -1)

    def landmark_list(self):
        return [(lm.x, lm.y, lm.z) for lm in self.landmarks.landmark]
    
    def is_valid_landmark(self, landmark):
        if not (0 <= landmark[0] <= 1) or not (0 <= landmark[1] <= 1):
            return False
        return True
    
    def center(self, center_organ):
        c1, c2 = center_organ()
        return ((c1[0] + c2[0]) / 2, (c1[1] + c2[1]) / 2)
    

    # Left and Right Shoulder Position
    def shoulder(self):
        landmark_list = self.landmark_list()
        left_shoulder = landmark_list[self.mp_pose.PoseLandmark.LEFT_SHOULDER.value]
        right_shoulder = landmark_list[self.mp_pose.PoseLandmark.RIGHT_SHOULDER.value]

        if not self.is_valid_landmark(left_shoulder) or not self.is_valid_landmark(right_shoulder):
            return None
  
        return left_shoulder, right_shoulder
    
    def z_shoulder(self):
        left_shoulder, right_shoulder = self.shoulder()
        return (left_shoulder[2] + right_shoulder[2]) / 2 
    
    # Left and Right Shoulder Hips Position
    def hips(self):
        landmark_list = self.landmark_list()
        left_hip = landmark_list[self.mp_pose.PoseLandmark.LEFT_HIP.value]
        right_hip = landmark_list[self.mp_pose.PoseLandmark.RIGHT_HIP.value]

        if not self.is_valid_landmark(left_hip) or not self.is_valid_landmark(right_hip):
            return None
        
        return left_hip, right_hip
    
    # Left and Right Shoulder Ear Position
    def ear(self):
        landmark_list = self.landmark_list()
        left_ear = landmark_list[self.mp_pose.PoseLandmark.LEFT_EAR.value]
        right_ear = landmark_list[self.mp_pose.PoseLandmark.RIGHT_EAR.value]

        if not self.is_valid_landmark(left_ear) or not self.is_valid_landmark(right_ear):
            return None
        
        return left_ear, right_ear

    
class HeartPosition(BodyLandmarkPosition):
    def __init__(self, landmarks, mp_pose, cv2, image):
        super().__init__(landmarks, mp_pose, cv2, image)

    def get_position(self):
        if  self.shoulder() is None or self.hips() is None:
            return None 
        # must have image same for height and width
        image_height, image_width, _ = self.image.shape

        center_shoulder = self.center(self.shoulder)
        center_hip = self.center(self.hips)

        x = int(center_shoulder[0] * image_width)
        y = int((center_shoulder[1] + (center_hip[1] - center_shoulder[1]) * 0.2) * image_height)
        z =  int(self.z_shoulder() * image_width)

        # For cv2 circle cordinatates
        heart_position = (x, y, z)
        self.cv2_circle(organ_postion=heart_position)

        # convert Unity coordinates
        normalized_x = center_shoulder[0]
        normalized_y = 1 - center_shoulder[1]  # Inverting y-coordinate

        x_unity = (normalized_x - 0.5) * 2
        y_unity = (normalized_y - 0.5) * 2

        x_unity_adjusted = x_unity * image_width / 100
        y_unity_adjusted = (y_unity * image_height / 100) - 1.6
        z_unity_adjusted = (((image_width + z) + 3) / 100) + 12

        position_dict = {'x': x_unity_adjusted, 'y': y_unity_adjusted, 'z': z_unity_adjusted}

        return position_dict

class BrainPosition(BodyLandmarkPosition):
    def __init__(self, landmarks, mp_pose, cv2, image):
        super().__init__(landmarks, mp_pose, cv2, image)

    def get_position(self):
        if  self.ear() is None:
            return None 
        # must have image same for height and width
        image_height, image_width, _ = self.image.shape
        center_ear = self.center(self.ear)
        landmark_list = self.landmark_list()
        nose = landmark_list[self.mp_pose.PoseLandmark.NOSE.value]

        x = int(center_ear[0] * image_width)
        y = int((center_ear[1] + (nose[1] - center_ear[1])) * image_height - 40)
        z =  int(self.z_shoulder() * image_width)

        # For cv2 circle cordinatates
        brain_position = (x, y)
        self.cv2_circle(organ_postion=brain_position)


        normalized_x = center_ear[0]
        normalized_y = 1 - center_ear[1]  # Inverting y-coordinate

        x_unity = (normalized_x - 0.5) * 2
        y_unity = (normalized_y - 0.5) * 2

        x_unity_adjusted = x_unity * image_width / 100
        y_unity_adjusted = (y_unity * image_height / 100) + 1.2
        z_unity_adjusted = (((image_width + z) + 3) / 100) + 12

        position_dict = {'x': x_unity_adjusted, 'y': y_unity_adjusted, 'z': z_unity_adjusted}

        return position_dict



def calculate_organ_position(organ_type, landmarks, mp_pose, cv2, image):
    if organ_type == 'heart':
        try:
            organ = HeartPosition(landmarks=landmarks, mp_pose=mp_pose, cv2=cv2, image=image)
            if organ.get_position() is None:
                print("Need Proper Position, this will send back to the client if possible")
            return organ.get_position()
        except Exception as e:
            print(e)

    if organ_type == 'brain':
        try:
            organ = BrainPosition(landmarks=landmarks, mp_pose=mp_pose, cv2=cv2, image=image)
            if organ.get_position() is None:
                print("Need Proper Position, this will send back to the client if possible")
            return organ.get_position()
        except Exception as e:
            print(e)