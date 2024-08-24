import os, shutil
import json
import time
from datetime import datetime

logs = "logs"
backup_logs = "backup-logs"
unity_logs = "DownloadedLogs"

logs_path =  os.path.join(os.path.dirname(__file__), "../", logs)
backup_logs_path = os.path.join(os.path.dirname(__file__), "../", backup_logs)
unity_logs_path =  os.path.join(os.path.dirname(__file__), "../", unity_logs)

path_logs_to_json =  os.path.join(os.path.dirname(__file__), "logsToJson")
if os.path.exists(path_logs_to_json):
   shutil.rmtree(path_logs_to_json)

os.makedirs(path_logs_to_json)

def logs_path_func():
   if os.path.exists(logs_path):
      print("Prepare for => ", logs_path)
      for sub in os.listdir(logs_path):
         sub_folder = os.path.join(logs_path, sub)
         files = os.listdir(sub_folder)
         for (root, dirs, filenames) in os.walk(sub_folder):
            if len(filenames) > 0:
               for idx, filename in enumerate(filenames):
                  file_path = os.path.join(root, filename)
                  f = open(file_path, "r")
                  lines = f.read().splitlines()

                  folder_name = root.replace(logs_path + "\\", "")
                  folder_logs_json = os.path.join(path_logs_to_json, logs, folder_name)
                  
                  if not os.path.exists(folder_logs_json):
                     os.makedirs(folder_logs_json)
                  
                  json_data = []
                  for line in lines:
                     try:
                        json_line = json.loads(line)
                        json_data.append(json_line)
                     except json.JSONDecodeError as e:
                        print(f"Error decoding JSON in file {file_path}: {e}")

                  file_log_json = os.path.join(folder_logs_json, filename.replace(".log", ".json"))

                  with open(file_log_json, "w") as json_file:
                     json_dump = json.dumps(json_data, indent=2)
                     json_file.write(json_dump)


def backup_logs_path_func():
   if os.path.exists(backup_logs_path):
      print("Prepare for => ", backup_logs_path)
      for sub in os.listdir(backup_logs_path):
         sub_layer1 = os.path.join(backup_logs_path, sub)
         sub_layer2 = os.listdir(sub_layer1)
         
         # print(sub_layer1, sub_layer2, backup_logs_path)
         for sub in sub_layer2:
            sub_layer2_path = os.path.join(sub_layer1, sub)
           
            for (root, dirs, filenames) in os.walk(sub_layer2_path):
               if len(filenames) > 0:
                  for idx, filename in enumerate(filenames):
                     # print(filename)
                     file_path = os.path.join(root, filename)
                     f = open(file_path, "r")
                     lines = f.read().splitlines()
                     
                     folder_name = root.replace(backup_logs_path + "\\", "")
                     folder_logs_json = os.path.join(path_logs_to_json, backup_logs, folder_name)
                    
                     
                     if not os.path.exists(folder_logs_json):
                        os.makedirs(folder_logs_json)
                     
                     json_data = []
                     for line in lines:
                        try:
                           json_line = json.loads(line)
                           json_data.append(json_line)
                        except json.JSONDecodeError as e:
                           print(f"Error decoding JSON in file {file_path}: {e}")

                     file_log_json = os.path.join(folder_logs_json, filename.replace(".log", ".json"))

                     with open(file_log_json, "w") as json_file:
                        json_dump = json.dumps(json_data, indent=2)
                        json_file.write(json_dump) 

def unity_logs_func():
   all_logs = []

   if os.path.exists(unity_logs_path):
      print("Prepare for => ", unity_logs_path)
      folder_logs_json = os.path.join(path_logs_to_json, unity_logs)
      if not os.path.exists(folder_logs_json):
         os.makedirs(folder_logs_json)

      for (root, dirs, filenames) in os.walk(unity_logs_path):
         if len(filenames) > 0:
            for idx, filename in enumerate(filenames):
               # print(filename)
               file_path = os.path.join(root, filename)
               f = open(file_path, "r")
               lines = f.read().splitlines()
               file_stats = os.stat(file_path)
               
               # file_size = file_stats.st_size
               last_modified = file_stats.st_mtime
               # creation_time = file_stats.st_ctime

               json_data = []
               for line in lines:
                  try:
                     json_line = json.loads(line)
                     json_data.append(json_line)
                     all_logs.append(json_line)
                  except json.JSONDecodeError as e:
                     print(f"Error decoding JSON in file {file_path}: {e}")

               file_log_json = os.path.join(folder_logs_json, filename.replace(".log", ".json"))
              

               with open(file_log_json, "w") as json_file:
                  json_dump = json.dumps(json_data, indent=2)
                  json_file.write(json_dump) 

      all_log_json = os.path.join(folder_logs_json, "zzz_all.json")
      with open(all_log_json, "w") as all_json:
         all_json_dump = json.dumps(all_logs, indent=2)
         all_json.write(all_json_dump) 

print("Converting logs to json")
unity_logs_func()
time.sleep(2)
logs_path_func()
time.sleep(2)
backup_logs_path_func()
print("Done converting logs to json")