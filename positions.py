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
    
    def center(self, landmark_pair):
        c1, c2 = landmark_pair
        return ((c1[0] + c2[0]) / 2, (c1[1] + c2[1]) / 2, (c1[2] + c2[2]) / 2)
    
    def landmark_pair(self, landmark1, landmark2):
        landmark_list = self.landmark_list()
        l1 = landmark_list[self.mp_pose.PoseLandmark[landmark1].value]
        l2 = landmark_list[self.mp_pose.PoseLandmark[landmark2].value]

        if not self.is_valid_landmark(l1) or not self.is_valid_landmark(l2):
            return None
  
        return l1, l2
    
    def calculate_organ_position(self, center1, center2, x_offset, y_offset):
        image_height, image_width, _ = self.image.shape
        x = int(center1[0] * image_width) + x_offset
        y = int((center1[1] + (center2[1] - center1[1]) ) * image_height + y_offset)
        z = int(center1[2] * image_width)

        self.cv2_circle(organ_postion=(x, y, z))
        return x, y, z

    def calculate_unity_coordinates(self, center, x_offset, y_offset, z_offset):
        image_height, image_width, _ = self.image.shape

        normalized_x = center[0]
        normalized_y = 1 - center[1]  # Inverting y-coordinate

        x_unity = (normalized_x - 0.5) * 2
        y_unity = (normalized_y - 0.5) * 2

        x_unity_adjusted = (x_unity * image_width / 100) + x_offset
        y_unity_adjusted = (y_unity * image_height / 100) + y_offset
        z_unity_adjusted = (((image_width * center[2]) + 3) / 300) + z_offset
    

        position_dict = { 'x': x_unity_adjusted, 'y': y_unity_adjusted, 'z': z_unity_adjusted }
    
        return position_dict


    
class HeartPosition(BodyLandmarkPosition):
    def __init__(self, landmarks, mp_pose, cv2, image):
        super().__init__(landmarks, mp_pose, cv2, image)

    def get_position(self):
        pair_shoulder = self.landmark_pair('LEFT_SHOULDER', 'RIGHT_SHOULDER')
        pair_hip = self.landmark_pair('LEFT_HIP', 'RIGHT_HIP')

        if pair_shoulder is None or pair_hip is None:
            return None 

        center_shoulder = self.center(pair_shoulder)
        center_hip = self.center(pair_hip)

        self.calculate_organ_position(center1=center_shoulder, center2=center_hip, x_offset=0, y_offset=-200)
        position_dict = self.calculate_unity_coordinates(center=center_shoulder, x_offset=0, y_offset=-1.4, z_offset=15)
        return position_dict

class BrainPosition(BodyLandmarkPosition):
    def __init__(self, landmarks, mp_pose, cv2, image):
        super().__init__(landmarks, mp_pose, cv2, image)

    def get_position(self):
        landmark_list = self.landmark_list()
        nose = landmark_list[self.mp_pose.PoseLandmark.NOSE.value]
        pair_ear = self.landmark_pair('LEFT_EAR', 'RIGHT_EAR')  

        if pair_ear is None:
            return None 
        
        center_ear = self.center(pair_ear)

        self.calculate_organ_position(center1=center_ear, center2=nose, x_offset=0, y_offset=- 50)
        position_dict = self.calculate_unity_coordinates(center=center_ear, x_offset=0, y_offset=+ 1.2, z_offset=15)
        return position_dict

class LiverPosition(BodyLandmarkPosition):
    def __init__(self, landmarks, mp_pose, cv2, image):
        super().__init__(landmarks, mp_pose, cv2, image)

    def get_position(self):
        pair_shoulder = self.landmark_pair('LEFT_SHOULDER', 'RIGHT_SHOULDER')
        pair_hip = self.landmark_pair('LEFT_HIP', 'RIGHT_HIP')

        if pair_shoulder is None or pair_hip is None:
            return None 

        center_shoulder = self.center(pair_shoulder)
        center_hip = self.center(pair_hip)

        self.calculate_organ_position(center1=center_shoulder, center2=center_hip, x_offset=-35, y_offset=-150)
        position_dict = self.calculate_unity_coordinates(center=center_shoulder, x_offset=-0.8, y_offset=-2, z_offset=15)
        return position_dict
class StomachPosition(BodyLandmarkPosition):
    def __init__(self, landmarks, mp_pose, cv2, image):
        super().__init__(landmarks, mp_pose, cv2, image)

    def get_position(self):
        pair_shoulder = self.landmark_pair('LEFT_SHOULDER', 'RIGHT_SHOULDER')
        pair_hip = self.landmark_pair('LEFT_HIP', 'RIGHT_HIP')

        if pair_shoulder is None or pair_hip is None:
            return None 

        center_shoulder = self.center(pair_shoulder)
        center_hip = self.center(pair_hip)

        self.calculate_organ_position(center1=center_shoulder, center2=center_hip, x_offset=30, y_offset=-145)
        position_dict = self.calculate_unity_coordinates(center=center_shoulder, x_offset=0.85, y_offset=-2.5, z_offset=15)
        return position_dict

class IntestinePosition(BodyLandmarkPosition):
    def __init__(self, landmarks, mp_pose, cv2, image):
        super().__init__(landmarks, mp_pose, cv2, image)

    def get_position(self):
        pair_shoulder = self.landmark_pair('LEFT_SHOULDER', 'RIGHT_SHOULDER')
        pair_hip = self.landmark_pair('LEFT_HIP', 'RIGHT_HIP')

        if pair_shoulder is None or pair_hip is None:
            return None 

        center_shoulder = self.center(pair_shoulder)
        center_hip = self.center(pair_hip)

        self.calculate_organ_position(center1=center_shoulder, center2=center_hip, x_offset=0, y_offset=-100)
        position_dict = self.calculate_unity_coordinates(center=center_shoulder, x_offset=0, y_offset=-2.8, z_offset=15)
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

    if organ_type == 'liver':
        try:
            organ = LiverPosition(landmarks=landmarks, mp_pose=mp_pose, cv2=cv2, image=image)
            if organ.get_position() is None:
                print("Need Proper Position, this will send back to the client if possible")
            return organ.get_position()
        except Exception as e:
            print(e)

    if organ_type == 'stomach':
        try:
            organ = StomachPosition(landmarks=landmarks, mp_pose=mp_pose, cv2=cv2, image=image)
            if organ.get_position() is None:
                print("Need Proper Position, this will send back to the client if possible")
            return organ.get_position()
        except Exception as e:
            print(e)
    if organ_type == 'intestine':
        try:
            organ = IntestinePosition(landmarks=landmarks, mp_pose=mp_pose, cv2=cv2, image=image)
            if organ.get_position() is None:
                print("Need Proper Position, this will send back to the client if possible")
            return organ.get_position()
        except Exception as e:
            print(e)