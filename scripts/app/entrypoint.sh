#!/bin/bash
gunicorn -c app.py app:app
