import numpy as np

class OrganPosition:
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
    
    def shoulder(self):
        landmark_list = self.landmark_list()
       
        left_shoulder = landmark_list[self.mp_pose.PoseLandmark.LEFT_SHOULDER.value]
        right_shoulder = landmark_list[self.mp_pose.PoseLandmark.RIGHT_SHOULDER.value]

        if not self.is_valid_landmark(left_shoulder) or not self.is_valid_landmark(right_shoulder):
            # print("Shoulder landmark are missing")
            return None
  
        return left_shoulder, right_shoulder
    

    def hips(self):
        landmark_list = self.landmark_list()
        left_hip = landmark_list[self.mp_pose.PoseLandmark.LEFT_HIP.value]
        right_hip = landmark_list[self.mp_pose.PoseLandmark.RIGHT_HIP.value]

        if not self.is_valid_landmark(left_hip) or not self.is_valid_landmark(right_hip):
            # print("Hips landmark are missing")
            return None
        return left_hip, right_hip
    
    def center_shoulder(self):
        left_shoulder, right_shoulder = self.shoulder()

        return ((left_shoulder[0] + right_shoulder[0]) / 2 , (left_shoulder[1] + right_shoulder[1]) / 2)

    def z_shoulder(self):
        left_shoulder, right_shoulder = self.shoulder()
        return (left_shoulder[2] + right_shoulder[2]) / 2 

    def center_hip(self):
        left_hip, right_hip = self.hips()
        return ((left_hip[0] + right_hip[0]) / 2, (left_hip[1] + right_hip[1]) / 2)


class HeartPosition(OrganPosition):
    def __init__(self, landmarks, mp_pose, cv2, image):
        super().__init__(landmarks, mp_pose, cv2, image)

    def get_position(self):
        if  self.shoulder() is None or self.hips() is None:
            return None
        
        # must have image same for height and width
        image_height, image_width, _ = self.image.shape
        center_shoulder = self.center_shoulder()
        center_hip = self.center_hip()

        x = int(center_shoulder[0] * image_width)
        y = int((center_shoulder[1] + (center_hip[1] - center_shoulder[1]) * 0.2) * image_height)
        z =  int(self.z_shoulder() * image_width)

        # For cv2 circle cordinatates
        heart_position = (x, y, z)
        self.cv2_circle(organ_postion=heart_position)

        # # for Unity cordinates
        # x_unity_adjusted = (x + 3) / 100
        # y_unity_adjusted = ((image_height - y) + 3 ) / 100
        # z_unity_adjusted = (((image_width + z) + 3) / 100) + 1.6 # continuous adjustment for distance 
        # position_dict = {'x' : x1, 'y' : y2, 'z' : z3}

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


def calculate_organ_position(organ_type, landmarks, mp_pose, cv2, image):
    if organ_type == 'heart':
        try:
            organ = HeartPosition(landmarks=landmarks, mp_pose=mp_pose, cv2=cv2, image=image)
            if organ.get_position() is None:
                print("Need Proper Position, this will send back to the client if possible")
            return organ.get_position()
        except Exception as e:
            print(e)



# class OrganPosition:
#     def __init__(self, landmarks, mp_pose, cv2, image):
#         self.landmarks = landmarks
#         self.mp_pose = mp_pose
#         self.cv2 = cv2
#         self.image = image

#     def landmarkList(self):
#         return [(lm.x, lm.y, lm.z) for lm in self.landmarks.landmark]
    
#     def cv2Circle(self, color=(0, 0, 255), organ_postion=None):
#         if organ_postion is not None:
#             image_height, image_width, _ = self.image.shape
#             self.cv2.circle(self.image, (int(organ_postion[0] * image_width), int(organ_postion[1] * image_height)), 10, color, -1)

#     def shoulder(self):
#         landmark_list = self.landmarkList()
#         left_shoulder = landmark_list[self.mp_pose.PoseLandmark.LEFT_SHOULDER.value]
#         right_shoulder = landmark_list[self.mp_pose.PoseLandmark.RIGHT_SHOULDER.value]

#         return left_shoulder, right_shoulder
    
#     def hips(self):
#         landmark_list = self.landmarkList()
#         left_hip = landmark_list[self.mp_pose.PoseLandmark.LEFT_HIP.value]
#         right_hip = landmark_list[self.mp_pose.PoseLandmark.RIGHT_HIP.value]

#         return left_hip, right_hip
    
#     def centerShoulder(self, h, w):
#         left_shoulder, right_shoulder = self.shoulder()
#         lsx = int(left_shoulder[0] * w)
#         lsy = int(left_shoulder[1] * h)
#         rsx = int(right_shoulder[0] * w)
#         rsy = int(right_shoulder[1] * h)
#         # return ((left_shoulder[0] + right_shoulder[0]) / 2, (left_shoulder[1] + right_shoulder[1]) / 2)
#         return ((lsx + rsx) / 2,  (lsy + rsy) / 2)

#     def zShoulder(self, h, w):
#         left_shoulder, right_shoulder = self.shoulder()
#         lsz = int(left_shoulder[2] * h)
#         rsz = int(right_shoulder[2] * h)
#         # return (left_shoulder[2] + right_shoulder[2]) / 2 
#         return (lsz + rsz) / 2
    
#     def centerHip(self, h, w):
#         left_hip, right_hip = self.hips()
#         lhx = int(left_hip[0] * w)
#         rhx = int(right_hip[0] * w)
#         lhy = int(left_hip[1] * h)
#         rhy = int(right_hip[1] * h)
#         # return ((left_hip[0] + right_hip[0]) / 2, (left_hip[1] + right_hip[1]) / 2)
#         return ((lhx + rhx) / 2, (lhy + rhy) / 2)

# class HeartPosition(OrganPosition):
#     def __init__(self, landmarks, mp_pose, cv2, image):
#         super().__init__(landmarks, mp_pose, cv2, image)

#     def getPosition(self):
#         h, w, c = self.image.shape
#         center_shoulder = self.centerShoulder(h, w)
#         center_hip = self.centerHip(h, w)
#         z_shoulder = self.zShoulder(h, w)

#         x = center_shoulder[0] / 100
#         y = (h - (center_shoulder[1] + (center_hip[1] - center_shoulder[1]) * 0.2)) / 100
#         z = z_shoulder / 100
#         heart_position = (x, y, z)
#         # heart_position = (center_shoulder[0] + (center_shoulder[0] - center_hip[0]) * 0.25, center_shoulder[1] + (center_hip[1] - center_shoulder[1]) * 0.2 )
#         # heart_position = (center_shoulder[0], center_shoulder[1] + (center_hip[1] - center_shoulder[1]) * 0.2,  self.zShoulder())
#         # print((heart_position[0]) * w, h - (heart_position[1] * h), heart_position[2] * w )
#         print(heart_position)
#         postion_dict = {'x' : heart_position[0], 'y' : heart_position[1], 'z' : heart_position[2]}
#         # self.cv2Circle(organ_postion=heart_position)
#         # print(postion_dict)
#         return postion_dict



# def calculateOrganPosition(organ_type, landmarks, mp_pose, cv2, image):
#     if organ_type == 'heart':
#         organ = HeartPosition(landmarks=landmarks, mp_pose=mp_pose, cv2=cv2, image=image)
#         return organ.getPosition()







            # if landmarks:
            #     # Convert landmarks to a more usable format
            #     landmark_list = [(lm.x, lm.y, lm.z) for lm in landmarks.landmark]
               
            #     # Shoulder
            #     left_shoulder = landmark_list[mp_pose.PoseLandmark.LEFT_SHOULDER.value]
            #     right_shoulder = landmark_list[mp_pose.PoseLandmark.RIGHT_SHOULDER.value]
            
            #     # Hip
            #     left_hip = landmark_list[mp_pose.PoseLandmark.LEFT_HIP.value]
            #     right_hip = landmark_list[mp_pose.PoseLandmark.RIGHT_HIP.value]

            #     center_shoulder = ((left_shoulder[0] + right_shoulder[0]) / 2, (left_shoulder[1] + right_shoulder[1]) / 2)
            #     center_hip = ((left_hip[0] + right_hip[0]) / 2, (left_hip[1] + right_hip[1]) / 2)
            #     print("left_shoulder", left_shoulder)
            #     print("right_shoulder", right_shoulder)
            #     print("center_shoulder",  center_shoulder)
            #     image_height, image_width, _ = image.shape

            #     heart_position = (center_shoulder[0], center_shoulder[1] + (center_hip[1] - center_shoulder[1]) * 0.3 )
            #     cv2.circle(image, (int(heart_position[0] * image_width), int(heart_position[1] * image_height)), 10, (0, 0, 255), -1)  # Red for heart

            #     # # Approximate center of the chest for heart and lungs
            #     # center_chest = (
            #     #     (left_shoulder[0] + right_shoulder[0]) / 2,
            #     #     (left_shoulder[1] + right_shoulder[1]) / 2
            #     # )

            #     # # Calculate heart and lungs positions
            #     # heart_position = (
            #     #     center_chest[0],
            #     #     center_chest[1] + (left_hip[1] - center_chest[1]) * 0.3  # Below the chest center
            #     # )
            #     # left_lung_position = (
            #     #     left_shoulder[0],
            #     #     left_shoulder[1] + (center_chest[1] - left_shoulder[1]) * 0.5
            #     # )
            #     # right_lung_position = (
            #     #     right_shoulder[0],
            #     #     right_shoulder[1] + (center_chest[1] - right_shoulder[1]) * 0.5
            #     # )

            #     # # Draw circles for heart and lungs
            #     # image_height, image_width, _ = image.shape
            #     # cv2.circle(image, (int(heart_position[0] * image_width), int(heart_position[1] * image_height)), 10, (0, 0, 255), -1)  # Red for heart
            #     # cv2.circle(image, (int(left_lung_position[0] * image_width), int(left_lung_position[1] * image_height)), 10, (255, 0, 0), -1)  # Blue for left lung
            #     # cv2.circle(image, (int(right_lung_position[0] * image_width), int(right_lung_position[1] * image_height)), 10, (255, 0, 0), -1)  # Blue for right lung
