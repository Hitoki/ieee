#!/bin/sh

export PYTHONPATH=..
export PYTHON_EGG_CACHE=/var/www/vhosts/systemicist.com/python-egg-cache

cat reset.sql
python manage.py dbshell < reset.sql
python manage.py reset --noinput ieeetags
python manage.py loaddata fixtures/data.json
python manage.py loaddata fixtures/data-small.json
