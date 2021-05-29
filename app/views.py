import errno
import os
import json
from secrets import token_hex

import flask

import pandas as pd
import plotly
from mongoengine import errors
from mongoengine.errors import ValidationError, SaveConditionError

from logger import logger
import models
import plotly.express as px
from datetime import datetime
from flask import render_template, request, session, jsonify, url_for, send_from_directory, flash
from werkzeug.utils import secure_filename, redirect
import bcrypt

from main import app

uploads_dir = app.config['UPLOADED_AUDIOS_DEST']
os.makedirs(uploads_dir, exist_ok=True)

ALLOWED_EXTENSIONS = {'mp3', 'wav', 'ogg'}


def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


@app.route('/find/<_id>', methods=['GET'])
def find(_id=None):
    if _id is None:
        return {
            'status_code': 400,
            'status_msg': 'Bad Request',
            'description': "Post id is required."
        }
    return models.get_upload_details(_id)


@app.route('/file/<_id>', methods=['GET'])
def get_file(_id):
    print(_id)
    return models.get_file(_id)


@app.route('/top_10', methods=['GET'])
def top_10():
    return models.get_top_10()


@app.route('/avg', methods=['GET'])
def avg():
    return models.get_average_file_size()


@app.route('/last_7_days_upload', methods=['GET'])
def last_7_days_upload():
    return models.last_7_days_upload()


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        users = models.Users
        login_user = users.objects(username=request.form['username']).first()
        if login_user and login_user['status'] == 1:
            if bcrypt.hashpw(request.form['password'].encode('utf-8'), login_user['password'].encode('utf-8')) == \
                    login_user['password'].encode('utf-8'):
                session['username'] = request.form['username']
                session['verified'] = True
                return redirect(url_for('index'))

    return render_template('login.html')


@app.route('/register', methods=['POST', 'GET'])
def register():
    required_fields = ['username', 'password', "confirm_password", "email"]
    if request.method == 'POST':
        if all(field in request.form for field in required_fields):
            if request.form['password'] == request.form['confirm_password']:
                print("OK")
                existing_user = models.Users.objects(username=request.form['username'],
                                                     password=request.form['password'])
                print(existing_user)
                if len(existing_user) == 0:
                    hash_pass = bcrypt.hashpw(request.form['password'].encode('utf-8'), bcrypt.gensalt())
                    try:
                        user = models.Users(username=request.form['username'], password=hash_pass,
                                            email=request.form['email'], verification_token=token_hex(25)).save()
                        print(user.verification_token)
                        if user and user.id:
                            session['username'] = request.form['username']
                    except SaveConditionError as e:
                        flash(f"Something going wrong. Unable to register . Error : {e}", category="error")
                        return render_template('register.html')
                    flash(
                        f"Your account has been successfully created. Please verify your account before continue. "
                        f"Verification mail has been sent to your email address",
                        category="success")
                    return redirect(url_for('index'))
                else:
                    flash(f"That username already exists!")
                    return render_template('register.html')
            else:
                flash("Password is not match", category="error")
                return render_template('register.html')
        else:
            flash("Pleaser fill all form fields", category="error")
            return redirect(url_for('register'))
    return render_template('register.html')


@app.route('/verify', methods=['GET'])
def verify():
    # Sample Url:
    # http://127.0.0.1:5000/verify?id=60b17819dbf1d5c899833a11&token=49c97c2abba5476ddcde29cac86f3266df75d1e5746fa434b1
    _ = request.args.get('id')
    token = request.args.get('token')
    if _ is not None and token is not None:
        users = models.Users
        login_user = users.objects(id=_).first()
        if str(token) == str(login_user['verification_token']):
            data = {"status": 1, "updated_at": datetime.now()}
            login_user.update(**data)
            flash("Your account has been successfully verified. Please log in", category="success")
            return render_template('login.html')


@app.route('/', methods=['GET', 'POST'])
def index():
    if 'username' not in session or session.get('username') == "" or "verified" not in session:
        return redirect(url_for('login'))
    # redis.incr('hits')
    # models.check_for_required_indexes()
    context = {
        "allowed": ', '.join(ALLOWED_EXTENSIONS),
        "title": "AudioServer",
        "my_url": "https://christosploutarchou.com",
        "copyright": f"© 2021 All rights reserved.",

    }
    # set session for image results
    if "file_urls" not in session:
        session['file_urls'] = []
    # list to hold our uploaded image urls

    # return dropzone template on GET request
    return render_template('index.html', data=context)


@app.route("/create_batch", methods=['POST'])
def create_batch():
    job_uuid = None
    entry_files = None
    return_response = flask.Response(status=500, response="Something going wrong. Please try again.")
    if request.method == 'POST':
        if "uuid" in request.form:
            job_uuid = request.form['uuid']
        if job_uuid is not None:
            try:
                entry_files = models.Files.objects(job_id=job_uuid)
                if len(entry_files) == 0:
                    return_response = flask.Response(status=409, response="No files found")
            except ValidationError as e:
                return_response = flask.Response(status=409, response=e.message)

            files = []
            for file in entry_files:
                files.append(str(file.id))
            if len(files) > 0:
                try:
                    inserted_batches = models.insert_batch(files)
                    if inserted_batches and len(inserted_batches) > 0:
                        try:
                            res = models.insert_upload(inserted_batches)
                            if res is not None:
                                return_response = flask.Response(status=200, response=str(res))
                        except SaveConditionError as e:
                            return_response = flask.Response(status=409, response=f"{e}")
                except SaveConditionError as e:
                    return_response = flask.Response(status=409, response=f"{e}")
    return return_response


@app.route("/stats")
def stats():
    context = {"top_10": models.get_top_10(),
               "title": "AudioServer",
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
    graph_json = json.dumps(fig, cls=plotly.utils.PlotlyJSONEncoder)
    header = "Weekly Uploads"
    description = """

        """
    return render_template('stats.html', data=context, graphJSON=graph_json, header=header, description=description)


@app.errorhandler(code_or_exception=404)
def html_error(e):
    # defining function
    return render_template("error.html", error=e)


@app.route("/upload", methods=["POST"])
def uploads():
    failed_files = []
    job_uuid = None
    if request.method == 'POST':
        files = request.files.getlist("file")
        if files is None:
            return jsonify(dict(code=400, msg="No Files"))

        if "uuid" in request.form:
            job_uuid = request.form['uuid']
        logger.info("test")
        target = f"{app.config['UPLOADED_AUDIOS_DEST']}/{job_uuid}"
        if job_uuid is None:
            return jsonify(dict(code=400, msg="Something going wrong."))
        try:
            os.mkdir(target)
        except OSError as exc:
            if exc.errno != errno.EEXIST:
                return ajax_response(False, f"Couldn't create upload directory: {target}")
            pass
        logger.info(files)
        for file in files:
            logger.info(file.filename)
            if file.filename == '':
                return jsonify(dict(code=400, msg="No valid file"))
            if file and allowed_file(file.filename):
                # save the file with to our Upload folder
                filename = secure_filename(file.filename)
                # exists = file.get(os.path.join(app.config['UPLOADED_AUDIOS_DEST'], filename))
                try:
                    file.save(os.path.join(target, filename))
                    from shutil import copyfileobj
                except OSError as error:
                    logger.info(f"Something going wrong. Unable to save filename. Error : {str(error)}")
                    failed_files.append(file)
                    continue
                size = os.path.getsize(target + "/" + filename)
                name, format_type = filename.split('.')
                file.close()
                data = {
                    "format_type": format_type,
                    'title': name,
                    'file_size': size,
                    "status": 1,
                    "updated_at": datetime.now(),
                    "job_id": str(job_uuid)
                }
                try:
                    models.insert_entry(data)
                except errors.SaveConditionError as e:
                    logger.error(f"Something went wrong. Error : {str(e)}")
                    failed_files.append(file)

            else:
                allowed = ', '.join(ALLOWED_EXTENSIONS)
                return jsonify(dict(code=400, msg=f"Allowed extensions file : {allowed}"))
        return ajax_response(200, 'ok')


@app.route('/render/<file_id>/<action>/', methods=['GET'])
def download(file_id, action):
    folder = models.Files.objects(id=file_id).first()

    filename = f"{folder['title']}.{folder['format_type']}"
    root = f"{app.config['UPLOADED_AUDIOS_DEST']}/{folder['job_id']}"
    if action.lower() == 'play':
        return send_from_directory(directory=root, path=filename)
    return send_from_directory(directory=root, path=filename, as_attachment=True)


def ajax_response(status, response):
    status_code = 201 if status else "error"
    return flask.Response(status=status_code, response=json.dumps(response))
