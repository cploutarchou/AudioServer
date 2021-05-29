import os
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

# Import all views in app
from views import *

if __name__ == "__main__":
    app.run(debug=True, port=5000, threaded=True)
else:
    app.run(host="172.21.0.25", port=5000)
