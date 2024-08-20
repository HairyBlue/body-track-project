import yaml
import os

# Cache the config to avoid unnecessary file reads
cached_config = None

default_settings_file = "./settings/default.settings.yaml"
adjustment_settings_file = "./settings/adjustment.settings.yaml"
offset_settings_file = "./settings/offset.settings.yaml"

def do_update_adjustment(configs, adjustment_settings):
   defaults = configs["default"]["settings"]
   adjustments = adjustment_settings["settings"]

   if adjustments is not None:
      for key, value in defaults.items():
         if isinstance(value, dict) and isinstance(adjustments[key], dict):
            if adjustments[key] is not None:
               configs["default"]["settings"][key] = adjustments[key]
 
   return configs
      
def svc_configs():
   global cached_config
   configs = {}

   # Grab config once to avoid O(N), and cache it
   if cached_config is None:
      if os.path.isfile(default_settings_file):
         with open(default_settings_file, 'r') as file:
            default_settings = yaml.safe_load(file)
            configs["default"] = default_settings
            
            if default_settings["settings"]["enable_adjustments_settings"]:
               with open(adjustment_settings_file, 'r') as file:
                  adjustment_settings = yaml.safe_load(file)
                  configs = do_update_adjustment(configs, adjustment_settings)
                  
      if os.path.isfile(offset_settings_file):
         with open(offset_settings_file, 'r') as file:
            offset_settings = yaml.safe_load(file)
            configs["offsets"] = offset_settings


      cached_config = configs
      print("configs has been cached")

   return cached_config