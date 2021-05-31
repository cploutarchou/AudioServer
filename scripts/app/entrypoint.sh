#!/bin/bash
gunicorn -c config.py main:app
