import yaml
import os
import pprint

default_settings_file = "./settings/default.settings.yaml"

def svc_configs():
   configs = {}

   if os.path.isfile(default_settings_file):
      with open(default_settings_file, 'r') as file:
         default_settings = yaml.safe_load(file)
         configs["default"] = default_settings

   return configs
