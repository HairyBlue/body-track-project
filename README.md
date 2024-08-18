# Body Tracking Project For Mobile Augmented Reality In Human Anatomy
This project demonstrates the use of body tracking in mobile augmented reality to study human anatomy. The application allows users to interact with anatomical models using real-time body movements.

## Prerequisites
- [Python](https://www.python.org/downloads/) (version 3.8 or higher)
- [Git](https://git-scm.com/downloads) (required for running bash scripts on Windows)

## Setting Up the Virtual Environment
To ensure consistency and manage dependencies, a Python virtual environment is recommended.
``` bash
python -m venv venv
source venv/Scripts/activate # When using windows
source venv/bin/activate # When using linux or mac
```

## Installation
After setting up the virtual environment, install the required dependencies listed in the requirements.txt file.
```bash
pip install -r requirements.txt
```

## Run Application
To launch the application and start the body tracking service, run:
```bash
python main.py
```

## Running Services with Bash (svc.sh)
For users on Windows, it's recommended to use Git Bash to execute bash scripts. This script automates building and managing the application services.

### Building services
To build the necessary components of the application, execute:
``` bash
./svc.sh build
```

### Start services
To start the application services, run:
``` bash
./svc.sh start
```

## Additional Resources
For further exploration of similar projects or additional modules related to mobile augmented reality and human anatomy, refer to the [Mobile Augmented Reality in Human Anatomy project repository](https://github.com/HairyBlue/unity_ar_human_anatomy).