import yaml
import os

default_settings_file = "./settings/default.settings.yaml"
adjustment_settings_file = "./settings/adjustment.settings.yaml"


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
   configs = {}

   if os.path.isfile(default_settings_file):
      with open(default_settings_file, 'r') as file:
         default_settings = yaml.safe_load(file)
         configs["default"] = default_settings

         if default_settings["settings"]["enable_adjustments_settings"]:
            with open(adjustment_settings_file, 'r') as file:
               adjustment_settings = yaml.safe_load(file)
               configs = do_update_adjustment(configs, adjustment_settings)


   return configs