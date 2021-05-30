import errno
import os
import json
from secrets import token_hex

import flask

import pandas as pd
import plotly
from mongoengine import errors
from mongoengine.errors import ValidationError, SaveConditionError

from common_functions import ALLOWED_EXTENSIONS, allowed_file
from logger import logger
import models
import plotly.express as px
from datetime import datetime
from flask import render_template, request, session, url_for, send_from_directory, flash
from werkzeug.utils import secure_filename, redirect
import bcrypt

from mailer import Mailer
from main import app

uploads_dir = app.config['UPLOADED_AUDIOS_DEST']
os.makedirs(uploads_dir, exist_ok=True)

failed_files = []


@app.route('/find/<_id>', methods=['GET'])
def find(_id=None):
    try:
        data = models.get_upload_details(_id)
    except Exception as e:
        return flask.Response(status=404, response=json.dumps(str(e)))
    return flask.Response(status=200, response=json.dumps(data))


@app.route('/file/<_id>', methods=['GET'])
def get_file(_id):
    try:
        data = models.get_file(_id)
    except Exception as e:
        return flask.Response(status=404, response=json.dumps(str(e)))
    return flask.Response(status=200, response=json.dumps(data))


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
    if is_logged_in() is True:
        return redirect(url_for('index'))
    if request.method == 'POST':
        users = models.Users
        login_user = users.objects(email=request.form['email']).first()
        if login_user and login_user['status'] == 1:
            if bcrypt.hashpw(request.form['password'].encode('utf-8'), login_user['password'].encode('utf-8')) == \
                    login_user['password'].encode('utf-8'):
                session['username'] = request.form['email']
                session['verified'] = True
                return redirect(url_for('index'))

    return render_template('login.html')


@app.route('/logout', methods=['GET'])
def logout():
    session.clear()
    return redirect(url_for("login"))


@app.route('/register', methods=['POST', 'GET'])
def register():
    if is_logged_in() is True:
        return redirect(url_for("login"))
    required_fields = ['password', "confirm_password", "email"]
    if request.method == 'POST':
        if all(field in request.form for field in required_fields):
            if request.form['password'] == request.form['confirm_password']:
                existing_user = models.Users.objects(email=request.form['email'],
                                                     password=request.form['password'])
                print(existing_user)
                if len(existing_user) == 0:
                    hash_pass = bcrypt.hashpw(
                        request.form['password'].encode('utf-8'), bcrypt.gensalt())
                    try:
                        user = models.Users(email=request.form['email'], password=hash_pass,
                                            verification_token=token_hex(25)).save()
                        print(user.verification_token)
                        if user and user.id:
                            session['username'] = request.form['email']
                    except SaveConditionError as e:
                        flash(
                            f"Something going wrong. Unable to register . Error : {e}", category="error")
                        return render_template('register.html')
                    flash(
                        f"Your account has been successfully created. Please verify your account before continue. "
                        f"Verification mail has been sent to your email address",
                        category="success")
                    url = f"{flask.request.host_url}/verify?id={user.id}&token={user.verification_token}"
                    mailer = Mailer()
                    mailer.set_to(to=[request.form['email']])
                    mailer.verify(url=url)
                    mailer.send()
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
    _ = request.args.get('id')
    token = request.args.get('token')
    if _ is not None and token is not None:
        users = models.Users
        login_user = users.objects(id=_).first()
        if str(token) == str(login_user['verification_token']):
            data = {"status": 1, "updated_at": datetime.now()}
            login_user.update(**data)
            flash("Your account has been successfully verified. Please log in",
                  category="success")
            return render_template('login.html')
        else:
            flash("Something going wrong. Unable to verify your account.",
                  category="error")
            return render_template('login.html')


@app.route('/', methods=['GET', 'POST'])
def index():
    if is_logged_in() is not True:
        return redirect(url_for("login"))
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
                if len(entry_files) == 0: return_response = flask.Response(status=409, response="No files found")
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
    available_objects = models.Files.objects().count()
    if is_logged_in() is not True:
        return redirect(url_for("login"))
    if available_objects > 0:
        context = {"top_10": models.get_top_10(),
                   "title": "AudioServer",
                   "average_file_size": avg()['AverageValue'],
                   "total_files": available_objects,
                   "total_size": models.convert_size(models.Files.objects.sum('file_size')),
                   "nodata": False
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
    else:
        return render_template('stats.html', data={"nodata": True, "title": "AudioServer", })


@app.errorhandler(code_or_exception=404)
def html_error(e):
    # defining function
    return render_template("error.html", error=e)


@app.route("/upload", methods=["POST"])
def uploads():
    job_uuid = None
    if request.method == 'POST':
        files = request.files.getlist("file")
        if files is None:
            return flask.Response(status=400, response=json.dumps("No Files available for upload"))
        if "uuid" in request.form:
            job_uuid = request.form['uuid']
        logger.info("test")
        target = f"{app.config['UPLOADED_AUDIOS_DEST']}/{job_uuid}"
        if job_uuid is None:
            return flask.Response(status=400, response=json.dumps("Something going wrong"))
        try:
            os.mkdir(target)
        except OSError as exc:
            if exc.errno != errno.EEXIST:
                return flask.Response(status=400, response=json.dumps(f"Couldn't create upload directory: {target}"))
            pass
        logger.info(files)
        for file in files:
            logger.info(file.filename)
            if file.filename == '':
                return flask.Response(status=400, response=json.dumps("No valid file"))
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
                return flask.Response(status=400,
                                      response=json.dumps(f"Not Allowed extension used for upload : {allowed}"))
        return flask.Response(status=200, response=json.dumps(f"OK"))


@app.route('/render/<file_id>/<action>/', methods=['GET'])
def download(file_id, action):
    folder = models.Files.objects(id=file_id).first()
    filename = f"{folder['title']}.{folder['format_type']}"
    root = f"{app.config['UPLOADED_AUDIOS_DEST']}/{folder['job_id']}"
    if action.lower() == 'play':
        return send_from_directory(directory=root, path=filename)
    return send_from_directory(directory=root, path=filename, as_attachment=True)


def is_logged_in():
    if 'username' in session and session.get('username') != "" and session.get("verified") is True:
        return True
    else:
        return False
