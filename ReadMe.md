# Setup guide

## Prerequisite
* python3

## Setup virtual environment
* python3 -m virtualenv venv
* . venv/bin/activate

## Install required library
* pip install pip --upgrade
* pip install -r requirements.txt

## Database migrate
* export FLASK_APP=run.py
* flask db migrate
* flask db upgrade
