import math
from config import svc_configs
import traceback
import numpy as np

configs = svc_configs()
default_settings  = configs["default"]["settings"]
offsets_settings = configs["offsets"]["settings"]

class BodyLandmarkPosition:
    def __init__(self, landmarks, mp_pose, cv2, image):
        self.landmarks = landmarks
        self.mp_pose = mp_pose
        self.cv2 = cv2
        self.image = image

    def image_shape(self):
        image_height, image_width, _ = self.image.shape
        return image_height, image_width
    
    def determine_aspect_ratio(self):
        image_height, image_width = self.image_shape()
        # landscape_aspect_ratio = image_width / image_height
        portrait_aspect_ratio = image_height / image_width
        aspect_ratio = portrait_aspect_ratio

        # Adjust if needed
        tolerance = 0.1

        aspect_ratio_list = offsets_settings["aspect_ratio_list"]
        
        for aspr in aspect_ratio_list:
            w, h = aspr.split("_by_")
            fw = float(w)
            fh = float(h)
            
            if abs(aspect_ratio - (fw / fh)) < tolerance:
                # remove print for production
                # print(aspr, " => ", [image_height, image_width, aspect_ratio]) 
                return aspr
           
        print("Aspect Ratio Not Identified. [image_height, image_width, aspect_ratio] =>", [image_height, image_width, aspect_ratio])
        return None

    def cv2_circle(self, color=(0, 0, 255), organ_position=None):
        if organ_position is not None:
            if len(organ_position) == 2:
                x, y = organ_position
                # Ensure x and y are integers
                x = int(x)
                y = int(y)
                
                self.cv2.circle(self.image, (x, y), 10, color, -1)

    def landmark_list(self):
        return [(lm.x, lm.y, lm.z) for lm in self.landmarks.landmark]
    
    def is_valid_landmark(self, landmark):
        if not (0 <= landmark[0] <= 1) or not (0 <= landmark[1] <= 1):
            return False
        return True
    
    def center(self, landmark_pair):
        c1, c2 = landmark_pair
        return ((c1[0] + c2[0]) / 2, (c1[1] + c2[1]) / 2, (c1[2] + c2[2]) / 2)
    
    def landmark_pair(self, landmark_name1, landmark_name2):
        landmark_list = self.landmark_list()
        l1 = landmark_list[self.mp_pose.PoseLandmark[landmark_name1].value]
        l2 = landmark_list[self.mp_pose.PoseLandmark[landmark_name2].value]

        if not self.is_valid_landmark(l1) or not self.is_valid_landmark(l2):
            return None
  
        return l1, l2
    
    def get_landmark(self, landmark_name):
        landmarks = self.landmark_list()
        landmark = landmarks[self.mp_pose.PoseLandmark[landmark_name].value]
        return landmark if 0 <= landmark[0] <= 1 and 0 <= landmark[1] <= 1 else None
    
    def calculate_organ_position(self, center1, center2, x_offset=0, y_offset=0, offset_calibration=None, estimate_distance=None):
        image_height, image_width = self.image_shape()

        x = 0
        y = 0
        z = 0

        if offset_calibration is not None and estimate_distance is not None:
            offsets =  ["x_offset", "y_offset"]
            offset_additional_stored = []

            for offset in offsets:
                if offset_calibration[offset]:
                    if not offset_calibration[offset]["enable"]:
                        offset_additional_stored.append(0)
                        continue
                    
                    operator = offset_calibration[offset]["operator"]
                    offset_additional = (estimate_distance - offset_calibration["minimum"]) * offset_calibration[offset]["common"]
                    
                    if operator == "subtraction":
                        offset_additional_stored.append(-offset_additional)
                    if operator == "addition":
                        offset_additional_stored.append(offset_additional)

            x_offset = x_offset + offset_additional_stored[0]
            y_offset = y_offset + offset_additional_stored[1]


            x = int(center1[0] * image_width) + x_offset
            y = int((center1[1] + (center2[1] - center1[1]) ) * image_height) + y_offset
            z = int(center1[2] * image_width)
        else:
            # fallback if None
            x = int(center1[0] * image_width) + x_offset
            y = int((center1[1] + (center2[1] - center1[1]) ) * image_height) + y_offset
            z = int(center1[2] * image_width)
            
        self.cv2_circle(organ_position=(x, y))
        return x, y, z

    def calculate_unity_coordinates(self, center, x_offset=0, y_offset=0, z_offset=0, offset_calibration=None, estimate_distance=None):
        image_height, image_width = self.image_shape()

        x_unity_adjusted = 0
        y_unity_adjusted = 0
        z_unity_adjusted = 0

        normalized_x = center[0]
        normalized_y = 1 - center[1]  # Inverting y-coordinate

        x_unity = (normalized_x - 0.5) * 2
        y_unity = (normalized_y - 0.5) * 2

        if offset_calibration is not None and estimate_distance is not None:
            offsets =  ["x_offset", "y_offset", "z_offset"]
            offset_additional_stored = []

            for offset in offsets:
                if offset_calibration[offset]:
                    if not offset_calibration[offset]["enable"]:
                        offset_additional_stored.append(0)
                        continue
                    
                    operator = offset_calibration[offset]["operator"]
                    offset_additional = (estimate_distance - offset_calibration["minimum"]) * offset_calibration[offset]["unity"]
                    
                    if operator == "subtraction":
                        offset_additional_stored.append(-offset_additional)
                    if operator == "addition":
                        offset_additional_stored.append(offset_additional)

            x_offset = x_offset + offset_additional_stored[0]
            y_offset = y_offset + offset_additional_stored[1]
            z_offset = z_offset + offset_additional_stored[2]

            x_unity_adjusted = round((x_unity * image_width / 100) + x_offset, 4)
            y_unity_adjusted = round((y_unity * image_height / 100) + y_offset, 4)
            z_unity_adjusted = math.floor((((image_width * center[2]) + 3) / 300) + z_offset)
        else:
            # fallback if None
            x_unity_adjusted = round((x_unity * image_width / 100) + x_offset, 4)
            y_unity_adjusted = round((y_unity * image_height / 100) + y_offset, 4)
            z_unity_adjusted = math.floor((((image_width * center[2]) + 3) / 300) + z_offset)

    

        position_dict = { 'x': x_unity_adjusted, 'y': y_unity_adjusted, 'z': z_unity_adjusted }
    
        return position_dict
    
    def validate_landmarks_list(self, landmarks_list):
        if len(landmarks_list) == 33:
            # print("Validation passed: 33 landmarks found.")
            return True
        else:
            # print(f"Validation failed: {len(landmarks_list)} landmarks found.")
            return False
    
    def all_unity_coordinates(self, x_offset=0, y_offset=0, z_offset=0, offset_calibration=None, estimate_distance=None):
        adjusted_landmarks = []

        landmarks_list = self.landmark_list()

        if self.validate_landmarks_list(landmarks_list=landmarks_list):
            for lm in landmarks_list:
                adjusted_landmark = self.calculate_unity_coordinates(lm, x_offset, y_offset, z_offset, offset_calibration, estimate_distance)
                adjusted_landmarks.append(adjusted_landmark)

            return adjusted_landmarks
        else:
            return None
    
    def calculate_pixel_distance(self, point1, point2):
        x1, y1 = point1
        x2, y2 = point2
        return np.sqrt((x2 - x1) ** 2 + (y2 - y1) ** 2)

    def calibrate_distance(self, pixel_distance, known_height_pixels, known_height_meters):
        # Convert pixel distance to real-world distance
        return (pixel_distance / known_height_pixels) * known_height_meters

    def estimate_distance(self, offset_calibration):
        Nose = self.get_landmark('NOSE')
        pair_foot = self.landmark_pair('LEFT_FOOT_INDEX', 'RIGHT_FOOT_INDEX') 

        if Nose and pair_foot:
            center_foot = self.center(pair_foot)

            # normalized the coordinates to pixel coordinates
            image_height, image_width = self.image.shape[:2]
            nose_pixel = (int(Nose[0] * image_width), int(Nose[1] * image_height))
            foot_pixel = (int(center_foot[0] * image_width), int(center_foot[1] * image_height))

            # Calc the pixel distance
            height_pixels = self.calculate_pixel_distance(nose_pixel, foot_pixel)
            
            # Calibration estimates
            known_height_pixels = 100
            known_height_meters = 1.75

            calibration = self.calibrate_distance(height_pixels, known_height_pixels, known_height_meters)

            # print(calibration)
            if calibration > offset_calibration["minimum"] and calibration < offset_calibration["maximum"]: 
                return calibration
    
            return None
    

class HeartPosition(BodyLandmarkPosition):
    def __init__(self, landmarks, mp_pose, cv2, image):
        super().__init__(landmarks, mp_pose, cv2, image)

    def get_position(self):
        selected_aspect_ratio =  self.determine_aspect_ratio()
        if selected_aspect_ratio is None:
            return None
        
        pair_shoulder = self.landmark_pair('LEFT_SHOULDER', 'RIGHT_SHOULDER')
        pair_hip = self.landmark_pair('LEFT_HIP', 'RIGHT_HIP')
        if pair_shoulder is None or pair_hip is None:
            return None

        center_shoulder = self.center(pair_shoulder)
        center_hip = self.center(pair_hip)
        
        offsets = offsets_settings["aspect_ratio"][selected_aspect_ratio]["heart"]
        offset_common = offsets["common"]
        offset_unity = offsets["unity"]
        offset_calibration = offsets["calibration"]

        estimate_distance = self.estimate_distance(offset_calibration)
        if estimate_distance is None:
            return default_settings["err_distance"]
        
        common_position =  self.calculate_organ_position(center1=center_shoulder, center2=center_hip, x_offset=offset_common["x_offset"], y_offset=offset_common["y_offset"], offset_calibration=offset_calibration, estimate_distance=estimate_distance)
        unity_position = self.calculate_unity_coordinates(center=center_shoulder, x_offset=offset_unity["x_offset"], y_offset=offset_unity["y_offset"], z_offset=offset_unity["z_offset"], offset_calibration=offset_calibration, estimate_distance=estimate_distance)
        return common_position, unity_position

class BrainPosition(BodyLandmarkPosition):
    def __init__(self, landmarks, mp_pose, cv2, image):
        super().__init__(landmarks, mp_pose, cv2, image)

    def get_position(self):
        selected_aspect_ratio =  self.determine_aspect_ratio()
        if selected_aspect_ratio is None:
            return None
               
        nose = self.get_landmark('NOSE')
        pair_ear = self.landmark_pair('LEFT_EAR', 'RIGHT_EAR')  
        if pair_ear is None or nose is None:
            return None 
        
        center_ear = self.center(pair_ear)
        
        offsets = offsets_settings["aspect_ratio"][selected_aspect_ratio]["brain"]
        offset_common = offsets["common"]
        offset_unity = offsets["unity"]
        offset_calibration = offsets["calibration"]

        estimate_distance = self.estimate_distance(offset_calibration)
        if estimate_distance is None:
            return default_settings["err_distance"]
        
        common_position = self.calculate_organ_position(center1=center_ear, center2=nose, x_offset=offset_common["x_offset"], y_offset=offset_common["y_offset"], offset_calibration=offset_calibration, estimate_distance=estimate_distance)
        unity_position = self.calculate_unity_coordinates(center=center_ear, x_offset=offset_unity["x_offset"], y_offset=offset_unity["y_offset"], z_offset=offset_unity["z_offset"], offset_calibration=offset_calibration, estimate_distance=estimate_distance)
        return common_position, unity_position

class LiverPosition(BodyLandmarkPosition):
    def __init__(self, landmarks, mp_pose, cv2, image):
        super().__init__(landmarks, mp_pose, cv2, image)

    def get_position(self):
        selected_aspect_ratio =  self.determine_aspect_ratio()
        if selected_aspect_ratio is None:
            return None
        
        pair_shoulder = self.landmark_pair('LEFT_SHOULDER', 'RIGHT_SHOULDER')
        pair_hip = self.landmark_pair('LEFT_HIP', 'RIGHT_HIP')
        if pair_shoulder is None or pair_hip is None:
            return None

        center_shoulder = self.center(pair_shoulder)
        center_hip = self.center(pair_hip)

        offsets = offsets_settings["aspect_ratio"][selected_aspect_ratio]["liver"]
        offset_common = offsets["common"]
        offset_unity = offsets["unity"]
        offset_calibration = offsets["calibration"]

        estimate_distance = self.estimate_distance(offset_calibration)
        if estimate_distance is None:
            return default_settings["err_distance"]
        
        common_position = self.calculate_organ_position(center1=center_shoulder, center2=center_hip, x_offset=offset_common["x_offset"], y_offset=offset_common["y_offset"], offset_calibration=offset_calibration, estimate_distance=estimate_distance)
        unity_position = self.calculate_unity_coordinates(center=center_shoulder, x_offset=offset_unity["x_offset"], y_offset=offset_unity["y_offset"], z_offset=offset_unity["z_offset"], offset_calibration=offset_calibration, estimate_distance=estimate_distance)
        return common_position, unity_position
    
class StomachPosition(BodyLandmarkPosition):
    def __init__(self, landmarks, mp_pose, cv2, image):
        super().__init__(landmarks, mp_pose, cv2, image)

    def get_position(self):
        selected_aspect_ratio =  self.determine_aspect_ratio()
        if selected_aspect_ratio is None:
            return None
        
        pair_shoulder = self.landmark_pair('LEFT_SHOULDER', 'RIGHT_SHOULDER')
        pair_hip = self.landmark_pair('LEFT_HIP', 'RIGHT_HIP')
        if pair_shoulder is None or pair_hip is None:
            return None 

        center_shoulder = self.center(pair_shoulder)
        center_hip = self.center(pair_hip)

        offsets = offsets_settings["aspect_ratio"][selected_aspect_ratio]["stomach"]
        offset_common = offsets["common"]
        offset_unity = offsets["unity"]
        offset_calibration = offsets["calibration"]
        
        estimate_distance = self.estimate_distance(offset_calibration)
        if estimate_distance is None:
            return default_settings["err_distance"]
        
        common_position = self.calculate_organ_position(center1=center_shoulder, center2=center_hip, x_offset=offset_common["x_offset"], y_offset=offset_common["y_offset"], offset_calibration=offset_calibration, estimate_distance=estimate_distance)
        unity_position = self.calculate_unity_coordinates(center=center_shoulder, x_offset=offset_unity["x_offset"], y_offset=offset_unity["y_offset"], z_offset=offset_unity["z_offset"], offset_calibration=offset_calibration, estimate_distance=estimate_distance)
        return common_position, unity_position

class IntestinePosition(BodyLandmarkPosition):
    def __init__(self, landmarks, mp_pose, cv2, image):
        super().__init__(landmarks, mp_pose, cv2, image)

    def get_position(self):
        selected_aspect_ratio =  self.determine_aspect_ratio()
        if selected_aspect_ratio is None:
            return None
        
        pair_shoulder = self.landmark_pair('LEFT_SHOULDER', 'RIGHT_SHOULDER')
        pair_hip = self.landmark_pair('LEFT_HIP', 'RIGHT_HIP')
        if pair_shoulder is None or pair_hip is None:
            return None

        center_shoulder = self.center(pair_shoulder)
        center_hip = self.center(pair_hip)

        offsets = offsets_settings["aspect_ratio"][selected_aspect_ratio]["intestine"]
        offset_common = offsets["common"]
        offset_unity = offsets["unity"]
        offset_calibration = offsets["calibration"]
        
        estimate_distance = self.estimate_distance(offset_calibration)
        if estimate_distance is None:
            return default_settings["err_distance"]
        
        common_position = self.calculate_organ_position(center1=center_shoulder, center2=center_hip, x_offset=offset_common["x_offset"], y_offset=offset_common["y_offset"], offset_calibration=offset_calibration, estimate_distance=estimate_distance)
        unity_position = self.calculate_unity_coordinates(center=center_shoulder, x_offset=offset_unity["x_offset"], y_offset=offset_unity["y_offset"], z_offset=offset_unity["z_offset"], offset_calibration=offset_calibration, estimate_distance=estimate_distance)
        return common_position, unity_position


# Calculate all body landmark  
class BodyPosition(BodyLandmarkPosition):
    def __init__(self, landmarks, mp_pose, cv2, image):
        super().__init__(landmarks, mp_pose, cv2, image)

    def get_position(self):
        selected_aspect_ratio =  self.determine_aspect_ratio()
        if selected_aspect_ratio is None:
            return None        

        offsets = offsets_settings["aspect_ratio"][selected_aspect_ratio]["body"]
        offset_unity = offsets["unity"]
        offset_calibration = offsets["calibration"]
        
        estimate_distance = self.estimate_distance(offset_calibration)
        if estimate_distance is None:
            return default_settings["err_distance"]
        
        all_unity_position = self.all_unity_coordinates(x_offset=offset_unity["x_offset"], y_offset=offset_unity["y_offset"], z_offset=offset_unity["z_offset"], offset_calibration=offset_calibration, estimate_distance=estimate_distance)

        if all_unity_position is None:
            return None
        
        selected_indices  = default_settings["selected_marks"]["body"]
        selected_landmarks  = [all_unity_position[i] for i in selected_indices]

        return None, selected_landmarks

# Only Calculate the selected body landmark
class BodyPositionV2(BodyLandmarkPosition):
    def __init__(self, landmarks, mp_pose, cv2, image):
        super().__init__(landmarks, mp_pose, cv2, image)

    def get_position(self):
        selected_position = []

        selected_aspect_ratio =  self.determine_aspect_ratio()
        if selected_aspect_ratio is None:
            return None  
        
        offsets = offsets_settings["aspect_ratio"][selected_aspect_ratio]["body"]
        offset_unity = offsets["unity"]
        offset_calibration = offsets["calibration"]
        
        estimate_distance = self.estimate_distance(offset_calibration)
        if estimate_distance is None:
            return default_settings["err_distance"]
        
        selected_body_marks = default_settings["selected_marks"]["body_v2"]

        landmarks_list = self.landmark_list()

        if self.validate_landmarks_list(landmarks_list=landmarks_list):
            for i in selected_body_marks:
                landmark = self.get_landmark(i)
                if landmark:
                    position_dict = self.calculate_unity_coordinates(landmark, x_offset=offset_unity["x_offset"], y_offset=offset_unity["y_offset"], z_offset=offset_unity["z_offset"], offset_calibration=offset_calibration, estimate_distance=estimate_distance)
                    selected_position.append(position_dict)
        
        return None, selected_position


    
def calculate_position(organ_type, landmarks, mp_pose, cv2, image):
    if organ_type == 'heart':
        try:
            organ = HeartPosition(landmarks=landmarks, mp_pose=mp_pose, cv2=cv2, image=image)
            common_position, unity_position = organ.get_position()

            if unity_position is None:
                print("Need Proper Position, this will send back to the client if possible")
            return unity_position
        except Exception as e:
            print(e)

    if organ_type == 'brain':
        try:
            organ = BrainPosition(landmarks=landmarks, mp_pose=mp_pose, cv2=cv2, image=image)
            common_position, unity_position = organ.get_position()

            if unity_position is None:
                print("Need Proper Position, this will send back to the client if possible")
            return unity_position
        except Exception as e:
            print(e)

    if organ_type == 'liver':
        try:
            organ = LiverPosition(landmarks=landmarks, mp_pose=mp_pose, cv2=cv2, image=image)
            common_position, unity_position = organ.get_position()

            if unity_position is None:
                print("Need Proper Position, this will send back to the client if possible")
            return unity_position
        except Exception as e:
            print(e)

    if organ_type == 'stomach':
        try:
            organ = StomachPosition(landmarks=landmarks, mp_pose=mp_pose, cv2=cv2, image=image)
            common_position, unity_position = organ.get_position()

            if unity_position is None:
                print("Need Proper Position, this will send back to the client if possible")
            return unity_position
        except Exception as e:
            print(e)
    if organ_type == 'intestine':
        try:
            organ = IntestinePosition(landmarks=landmarks, mp_pose=mp_pose, cv2=cv2, image=image)
            common_position, unity_position = organ.get_position()

            if unity_position is None:
                print("Need Proper Position, this will send back to the client if possible")
            return unity_position
        except Exception as e:
            print(e)

def calculate_position_v2(oType, args):
        try:
            heart = HeartPosition
            brain = BrainPosition
            liver = LiverPosition
            stomach =  StomachPosition
            intestine = IntestinePosition
            body = BodyPosition
            # body_v2 = BodyPositionV2

            organs = {
                'heart': heart,
                'brain': brain,
                'liver': liver,
                'stomach': stomach,
                'intestine': intestine,
                'body': body
            }
            
            organ_cls = organs[oType]
            return organ_cls(**args).get_position()
        except Exception as e:
            print("Unable to calculate organ position => ",  e)
            traceback.print_exc()