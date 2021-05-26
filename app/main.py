import os
import flask_mongoengine
from flask import Flask

app = Flask(__name__, static_folder='static', template_folder='templates')

app.config['SECRET_KEY'] = 'supersecretkeygoeshere'
# Uploads settings
app.config['UPLOADED_AUDIOS_DEST'] = os.path.join(app.root_path, 'uploads')
app.config['MONGODB_HOST'] = '172.21.0.11'
app.config['MONGODB_PORT'] = 27017
app.config['MONGODB_DB'] = 'AudioServer'
app.config['MONGODB_CONNECT'] = False
db = flask_mongoengine.MongoEngine()
db.init_app(app)

# Import all views in app
from views import *

if __name__ == "__main__":
    app.run(debug=True)