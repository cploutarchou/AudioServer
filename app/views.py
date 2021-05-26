import os
import json
import pandas as pd
import plotly
from logger import logger
import models
import plotly.express as px
from datetime import datetime
from flask import render_template, request, redirect, session, flash
from werkzeug.utils import secure_filename

from main import app

uploads_dir = app.config['UPLOADED_AUDIOS_DEST']
os.makedirs(uploads_dir, exist_ok=True)

ALLOWED_EXTENSIONS = set(['mp3', 'wav', 'ogg'])


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


@app.route('/', methods=['GET', 'POST'])
def index():
    # redis.incr('hits')
    # models.check_for_required_indexes()
    context = {
        "allowed": ', '.join(ALLOWED_EXTENSIONS),
        "my_url": "https://christosploutarchou.com",
        "copyright": f"© 2021 All rights reserved.",

    }
    # set session for image results
    if "file_urls" not in session:
        session['file_urls'] = []
    # list to hold our uploaded image urls
    file_urls = session['file_urls']
    failed = []
    # handle image upload from Drop-zone
    if request.method == 'POST':
        if 'files[]' not in request.files:
            flash('No file part')
            return redirect(request.url)
        files = request.files.getlist('files[]')
        entry_files = []
        upload_batches = []
        for file in files:
            if file.filename == '':
                flash(message='No file selected for uploading', category='error')
                return redirect(request.url)
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
                object_id = models.insert_entry(data)

                if object_id is not None:
                    entry_files.append(str(object_id))
                    logger.info(f"File {filename} successfully uploaded.")
                else:
                    failed.append(filename)

                flash('File(s) successfully uploaded')
            else:
                flash(f"Allowed file types are {context['allowed']}")
                return redirect(request.url)
                # append image url
            file_urls.append(filename)
        if len(entry_files) > 0:
            inserted_batches = models.insert_batch(entry_files)
            if len(inserted_batches) > 0:
                res = models.insert_upload(inserted_batches)
                context['uploaded_id'] = res
        return render_template('index.html', data=context)
    # return dropzone template on GET request
    return render_template('index.html', data=context)


# app name
@app.errorhandler(404)
def not_found(e):
    # defining function
    return render_template("404.html", error=e)


@app.route("/stats")
def stats():
    context = {"top_10": models.get_top_10(),
               "average_file_size": avg()['AverageValue'],
               "total_files": models.Files.objects().count(),
               "total_size": models.convert_size(models.Files.objects.sum('file_size'))
               }
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
    return render_template('stats.html', data=context, graphJSON=graphJSON, header=header, description=description)
