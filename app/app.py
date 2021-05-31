import multiprocessing
import os
from distutils.util import strtobool

import flask_mongoengine
from flask import Flask
import config as conf

app = Flask(__name__, static_folder='static', template_folder='templates')

app.config['SECRET_KEY'] = conf.secret
# Uploads settings
app.config['UPLOADED_AUDIOS_DEST'] = os.path.join(app.root_path, conf.upload_dir)
app.config['MONGODB_HOST'] = conf.mongo_host
app.config['MONGODB_PORT'] = int(conf.mongodb_port)
app.config['MONGODB_DB'] = conf.mongo_db
app.config['MONGODB_CONNECT'] = conf.mongo_connect
db = flask_mongoengine.MongoEngine()
db.init_app(app)

from views import *

bind = os.getenv('WEB_BIND', '172.21.0.25:5000')
accesslog = '-'
access_log_format = "%(h)s %(l)s %(u)s %(t)s '%(r)s' %(s)s %(b)s '%(f)s' '%(a)s' in %(D)sµs"

workers = int(os.getenv('WEB_CONCURRENCY', multiprocessing.cpu_count() * 2))
threads = int(os.getenv('PYTHON_MAX_THREADS', 4))

reload = bool(strtobool(os.getenv('WEB_RELOAD', 'false')))
