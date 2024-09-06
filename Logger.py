import logging
from logging.handlers import RotatingFileHandler
import json
import os
from datetime import datetime
import math
from config import svc_configs
import sys

base_filename = "app.log"
folder_path = "logs"

folder_path_calc_response_time = os.path.join(folder_path, "calc-response-time")
folder_path_quizz = os.path.join(folder_path, "quizz")
folder_path_svc = os.path.join(folder_path, "svc")

if not os.path.exists(folder_path):
   os.makedirs(folder_path)

if not os.path.exists(folder_path_calc_response_time):
   os.makedirs(folder_path_calc_response_time)

if not os.path.exists(folder_path_quizz):
   os.makedirs(folder_path_quizz)

if not os.path.exists(folder_path_svc):
   os.makedirs(folder_path_svc)


configs = svc_configs()
default_settings  = configs["default"]["settings"]

class JsonFormatter(logging.Formatter):
   def __init__(self, extra_fields=None, *args, **kwargs):
      super().__init__(*args, **kwargs)
      self.extra_fields = extra_fields if extra_fields else []

   def format(self, record):

      log_record = {
         # "timestamp": self.formatTime(record, self.datefmt),
         "level": record.levelname,
         "message": record.getMessage(),
         # "module": record.module,
         # "function": record.funcName,
         # "line": record.lineno,
         # "name": record.name,
      }

      for field in self.extra_fields:
         log_record[field] = getattr(record, field, None)

      return json.dumps(log_record)

class SVCJsonFormatter(logging.Formatter):
   def __init__(self, extra_fields=None, *args, **kwargs):
      super().__init__(*args, **kwargs)
      self.extra_fields = extra_fields if extra_fields else []

   def format(self, record):
      
      log_record = {
         # "timestamp": self.formatTime(record, self.datefmt),
         "level": record.levelname,
         "message": record.getMessage(),
         # "module": record.module,
         # "function": record.funcName,
         # "line": record.lineno,
         # "name": record.name,
      }

      for field in self.extra_fields:
         log_record[field] = getattr(record, field, None)

      return json.dumps(log_record)
   
class DateRotatingFileHandler(RotatingFileHandler):
    def doRollover(self):
      self.stream.close()

      current_time = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
     
      log_dir, base_filename = os.path.split(self.baseFilename)
     

      new_log_file = f"log-{current_time}.log"
      new_log_file_path = os.path.join(log_dir, new_log_file)

      if os.path.exists(new_log_file_path):
         os.remove(new_log_file_path)
      
      os.rename(self.baseFilename, new_log_file_path)

      self.mode = "a"
      self.stream = self._open()


def setup_logger_rts(extra_fields=None):
    log_path = os.path.join(folder_path_calc_response_time, base_filename)

    logger = logging.getLogger("JsonLogger")
    logger.setLevel(logging.DEBUG)
    
    for handler in logger.handlers[:]:
        logger.removeHandler(handler)
    
    handler = DateRotatingFileHandler(
        log_path, maxBytes=50 * 1024, backupCount=0
    )

    json_formatter = JsonFormatter(extra_fields=extra_fields)
    handler.setFormatter(json_formatter)  # Formatter set here

    logger.addHandler(handler)

    return logger

def setup_logger_quizz(user_uuid, extra_fields=None):
   log_path = os.path.join(folder_path_quizz, f"{user_uuid}.log")

   logger = logging.getLogger("JsonLogger")
   logger.setLevel(logging.DEBUG)

   for handler in logger.handlers[:]:
      logger.removeHandler(handler)

   handler = logging.FileHandler(log_path)
   handler.setLevel(logging.DEBUG)

   json_formatter = JsonFormatter(extra_fields=extra_fields)
   handler.setFormatter(json_formatter)

   logger.addHandler(handler)

   return logger


def setup_logger_svc(extra_fields=None):
   log_path = os.path.join(folder_path_svc, "svc.log")

   logger = logging.getLogger("JsonLogger")
   logger.setLevel(logging.DEBUG)

   for handler in logger.handlers[:]:
      logger.removeHandler(handler)

   json_formatter = SVCJsonFormatter(extra_fields=extra_fields)

   handler = logging.FileHandler(log_path)
   handler.setLevel(logging.DEBUG)
   handler.setFormatter(json_formatter)
   logger.addHandler(handler)

   if default_settings["print_svc_logger"]:
      stdout_handler = logging.StreamHandler(sys.stdout)
      stdout_handler.setLevel(logging.DEBUG)
      stdout_handler.setFormatter(json_formatter)
      logger.addHandler(stdout_handler)

   return logger

def calc_time_and_log(topic=None, role=None, start_time=0, end_time=0):
   time_difference_ms = (end_time - start_time) * 1000
   
   args = {
      "start_time": start_time,
      "end_time": end_time,
      "time_difference_ms": round(time_difference_ms, 2),
      "topic": topic,
      "role": role
   }

   extra_fields = ["start_time", "end_time", "time_difference_ms", "topic", "role"]

   logger = setup_logger_rts(extra_fields=extra_fields)

   logger.info("log time difference of calculating frame", extra=args)

