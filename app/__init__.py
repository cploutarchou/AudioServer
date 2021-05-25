import json
import os

import pandas as pd
import plotly
from flask import Flask, redirect, render_template, request, session, flash
from pymongo import MongoClient
from werkzeug.utils import secure_filename
import plotly.express as px

app = Flask(__name__, static_folder='static', template_folder='templates')

app.config['SECRET_KEY'] = 'supersecretkeygoeshere'
# Uploads settings
app.config['UPLOADED_AUDIOS_DEST'] = os.getcwd() + '/uploads'

ALLOWED_EXTENSIONS = set(['mp3', 'wav', 'ogg'])

client = MongoClient(port=27017, host='localhost')
db = client['AudioServer']
from app.models import *


def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


@app.route('/find/<id>', methods=['GET'])
def find(id=None):
    if id is None:
        return {
            'status_code': 400,
            'status_msg': 'Bad Request',
            'description': "Post id is required."
        }
    return models.get_upload_details(id)


@app.route('/file/<id>', methods=['GET'])
def get_file(id):
    if id is None:
        return {
            'status_code': 400,
            'status_msg': 'Bad Request',
            'description': "Post id is required."
        }
    return models.get_file(id)


@app.route('/top_10', methods=['GET'])
def top_10():
    return models.get_top_10()


@app.route('/avg', methods=['GET'])
def avg():
    return models.get_average_file_size()


@app.route('/last_7_days_upload', methods=['GET'])
def last_7_days_upload():
    return models.last_7_days_upload()


@app.route('/chart')
def chart():
    data = last_7_days_upload()
    df = pd.DataFrame(data['data'])
    fig = px.bar(df, x='date', y='items', barmode='stack',
                 hover_data=['date', 'items'], color='date',
                 labels={'pop': 'population of Canada'}, height=350)

    fig.update_layout(barmode='stack')
    fig.update_xaxes(categoryorder='category ascending')
    graphJSON = json.dumps(fig, cls=plotly.utils.PlotlyJSONEncoder)
    header = "Weekly Uploads"
    description = """
  
    """
    return render_template('dash.html', graphJSON=graphJSON, header=header, description=description)


@app.route('/', methods=['GET', 'POST'])
def index():
    context = {"allowed": ', '.join(ALLOWED_EXTENSIONS)}
    # set session for image results
    if "file_urls" not in session:
        session['file_urls'] = []
    # list to hold our uploaded image urls
    file_urls = session['file_urls']

    # handle image upload from Drop-zone
    if request.method == 'POST':
        if 'files[]' not in request.files:
            flash('No file part')
            return redirect(request.url)
        files = request.files.getlist('files[]')
        entry_files = []
        upload_batches = []
        for file in files:
            print(file.filename)
            if file.filename == '':
                flash(message='No file selected for uploading', category='error')
                return redirect(request.url)
            print(allowed_file(file.filename))
            if file and allowed_file(file.filename):
                # save the file with to our Upload folder
                filename = secure_filename(file.filename)
                # exists = file.get(os.path.join(app.config['UPLOADED_AUDIOS_DEST'], filename))
                file.save(os.path.join(app.config['UPLOADED_AUDIOS_DEST'], filename))
                os.path.getsize(app.config['UPLOADED_AUDIOS_DEST'] + "/" + filename)
                size = os.path.getsize(app.config['UPLOADED_AUDIOS_DEST'] + "/" + filename)
                name, type = filename.split('.')
                data = {
                    "format_type": type,
                    'title': name,
                    'file_size': size,
                    "status": 1,
                    "updated_at": datetime.now()
                }
                object_id = insert_entry(data)

                if object_id is not None:
                    entry_files.append(str(object_id))
                    flash(f"Something going wrong unable to save {filename} data to database")

                flash('File(s) successfully uploaded')
            else:
                flash(f"Allowed file types are {context['allowed']}")
                return redirect(request.url)
                # append image url
            file_urls.append(filename)
        if len(entry_files) > 0:
            inserted_batches = insert_batch(entry_files)
            if len(inserted_batches) > 0:
                res = insert_upload(inserted_batches)
                return res
        return render_template('index.html', data=context)
    # return dropzone template on GET request
    return render_template('index.html', data=context)


# app name
@app.errorhandler(404)
def not_found(e):
    # defining function
    return render_template("404.html", error=e)
