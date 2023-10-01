#!/bin/bash 

if [ ! -d "venv" ]
then
  echo "Missing venv, installing"
  python3 -m venv venv

  echo "installing dependencies"
  ./venv/bin/pip3 install -r requirements.txt
fi

[ ! -d "venv" ] && echo "Error while creating venv, check errors" && exit 1
