#!/bin/bash

venv_dir="env"

if [ ! -d $venv_dir ]; then
  python3 -m pip install --upgrade pip
  python3 -m pip install --user virtualenv
  python3 -m venv $venv_dir
  source $venv_dir/bin/activate
  pip install -r requirements.txt
fi

source $venv_dir/bin/activate