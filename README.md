# Body Tacking Project

## Prerequisites
[python](https://www.python.org/downloads/) min version requirement `>=3.8`

## Activate Virtualization
``` python
python -m venv venv
source venv/Scripts/activate # When using windows
source venv/bin/activate # When using linux or mac
```

## Installation
```
pip install -r requirements.txt
```

## Run services
```
python main.py
```


## Using bash (svc.sh)
Prerequisites: install [git bash]() when using windows
Used git bash as your terminal

### Building services
``` bash
./svc.sh build
```
### Start services
``` bash
./svc.sh start
```
