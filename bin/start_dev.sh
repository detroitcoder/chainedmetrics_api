#!/usr/bin/env bash

cd ./src

conda run --no-capture-output -n app gunicorn -c gunicorn_config.py wsgi