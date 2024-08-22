# Body Tracking Project For Mobile Augmented Reality In Human Anatomy (￣▽￣)ノ
This project demonstrates the use of body tracking in mobile augmented reality to study human anatomy. The application allows users to interact with anatomical models using real-time body movements.

## Prerequisites (°ロ°)☝
- [Python](https://www.python.org/downloads/) (version 3.8 or higher)
- [Git](https://git-scm.com/downloads) (required for running bash scripts on Windows)



## Setting Up the Virtual Environment (O_O;) 
To ensure consistency and manage dependencies, a Python virtual environment is recommended. Follow these steps to set up and activate the virtual environment.

### Create the Virtual Environment (ᵔ ͜ʖ ͡ᵔ)
Run the following command to create a virtual environment named venv:
``` bash
python -m venv venv
```
### Activate the virtual environment (ಠ_ಠ)
On Windows
``` bash
# Command Prompt or PowerShell
.\venv\Scripts\activate # Or venv\Scripts\activate or activate
# Git Bash
source ./venv/Scripts/activate # Or source venv/Scripts/activate 
```

On Linux or macOS
``` bash
source venv/bin/activate 
```

## Installation (＾◡＾)
After setting up the virtual environment, install the required dependencies listed in the requirements.txt file.
```bash
pip install -r requirements.txt
```

### Troubleshooting Installation Errors (ノಠ益ಠ)ノ
If you encounter an error during installation and the virtual environment has been activated, try the following steps:\
On Windows
``` bash
# Command Prompt or PowerShell
.\venv\Scripts\python -m pip install -r requirements.txt # Or venv\Scripts\python -m pip install -r requirements.txt
# Git Bash
./venv/Scripts/python -m pip install -r requirements.txt # Or venv/Scripts/python  -m pip install -r requirements.txt
```

When using Linux or macOS
``` bash
venv/bin/activate -m pip install -r requirements.txt
```

## Run Application (´｡• ᵕ •｡`)
To launch the application and start the body tracking service, run:
```bash
python main.py
```

## Running Services with Bash (svc.sh) (°o°:)
For users on Windows, it's recommended to use Git Bash to execute bash scripts. This script automates building and managing the application services.

### Building services (⌐■_■)
To build the necessary components of the application, execute:
``` bash
./svc.sh build
```

### Start services (￣ー￣)
To start the application services, run:
``` bash
./svc.sh start
```

## Deactivate the virtual environment (￣▽￣*)ゞ
To deactivate the virtual environment and return to the global Python environment, simply run:
``` bash
deactivate
```

## Additional Resources (o^▽^o)
For further exploration of similar projects or additional modules related to mobile augmented reality and human anatomy, refer to the [unity-ar-human-anatomy](https://github.com/HairyBlue/unity-ar-human-anatomy).
