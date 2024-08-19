#!/bin/bash
set -e

backup='backup-logs'
timestamp=$(date +"%Y%m%d_%H%M%S")


if [[ ! -d  "$backup" ]]; then
   mkdir $backup
fi

if [[ -d 'logs' ]]; then
   if [[ "$(ls -A logs)" ]]; then
      echo "create backup for logs"
      bkp="$backup/$timestamp-bkp"
      mkdir $bkp
      cp -r logs/* $bkp
   fi
 
   rm -rf logs
fi

if [[ -d 'output.log' ]]; then
   rm output.log
fi

mkdir logs
touch output.log

function die() {
   echo "$1"
   exit 1
}

function fbuild() {
   if [[ ! -d "venv" ]]; then
      python -m venv venv || die "unable to create venv"
   fi
   
   if [[ -d "venv/Scripts" ]]; then
      source venv/Scripts/activate
      sleep 2
      ./venv/Scripts/python -m pip install -r requirements.txt || die "unable to install requirements"
   elif [[ -d "venv/bin" ]]; then
      source venv/bin/activate
      sleep 2
      ./venv/bin/python -m pip install -r requirements.txt || die "unable to install requirements"
   fi
}


function fstart() {
   if [[ -d "venv/Scripts" ]]; then
      ./venv/Scripts/python main.py 2> output.log
      if [[ $? -ne 0 ]]; then
         echo "Error occurred while running main.py. See output.log for details."
         cat output.log
         exit 1
      fi
   elif [[ -d "venv/bin" ]]; then
      ./venv/bin/python main.py 2> output.log 
      if [[ $? -ne 0 ]]; then
         echo "Error occurred while running main.py. See output.log for details."
         cat output.log
         exit 1
      fi
   else 
      die "Virtual environment not found. Build first"
   fi
}

function freeze() {
   if [[ -d "venv/Scripts" ]]; then
      ./venv/Scripts/python -m pip freeze > requirements.tx
   elif [[ -d "venv/bin" ]]; then
      ./venv/bin/python -m pip freeze > requirements.tx
   else 
      die "Virtual environment not found. Build first"
   fi
}

function finstall() {
   if [[ -d "venv/Scripts" ]]; then
      ./venv/Scripts/python -m pip install "$1" || die "unable to install"
   elif [[ -d "venv/bin" ]]; then
      ./venv/bin/python -m pip install "$1" || die "unable to install"
   else 
      die "Virtual environment not found. Build first"
   fi
}

if [[ "$1" == "build" ]]; then
   fbuild
elif [[ "$1" == "start" ]]; then
   fstart
elif [[ "$1" == "freeze" ]]; then
   freeze
elif [[ "$1" == "install" ]]; then
   finstall $2
elif [[ "$1" == "rbkp" ]]; then
   rm -rf "$backup"
else
   echo "build       - build the service, this will activate virtual environment and install dependencies"
   echo "start       - start services"
   echo "freeze      - generate a requirements.txt file"
   echo "install     - install neccessary dependencies. Usage: ./svc.sh install <package-name> | ./svc.sh install cv2"
   echo "rbkp        - remove backup folder"
fi