import math
import os
from pprint import pprint

from flask import render_template, request, redirect, url_for
from werkzeug.utils import secure_filename

from app import app, models

uploads_dir = app.config['UPLOADED_AUDIO_DEST']
os.makedirs(uploads_dir, exist_ok=True)

ALLOWED_EXTENSIONS = set(['txt', 'pdf', 'png', 'jpg', 'jpeg', 'gif'])


@app.route("/")
def index():
    return render_template("index.html")


def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1] in ALLOWED_EXTENSIONS


def convert_size(size_bytes):
    if size_bytes == 0:
        return "0B"
    size_name = ("B", "KB", "MB", "GB", "TB", "PB", "EB", "ZB", "YB")
    i = int(math.floor(math.log(size_bytes, 1024)))
    p = math.pow(1024, i)
    s = round(size_bytes / p, 2)
    return f"{s} {size_name[i]}"


# @app.route('/upload', methods=['POST'])
# def upload_file():
#     uploaded_file = request.files.get('file')
#     print(type(uploaded_file))
#     exit(0)
#     if uploaded_file.filename != '':
#         f = mutagen.File(uploaded_file)
#         print(f.info.pprint())
#         print(f.mime)
#         print(f.values())
#         pprint(uploaded_file.filename)
#         file = uploaded_file.filename.rsplit('.')
#         filename = file[0]
#         file_format = file[1]
#
#         print(f"Filename {filename}")
#         print(f"fileformat: {file_format}")
#         uploaded_file.save(os.path.join(uploads_dir, secure_filename(uploaded_file.filename)), buffer_size=163840)
#         print(
#             f"File SIZE : {convert_size(os.stat(f'{uploads_dir}/{secure_filename(uploaded_file.filename)}').st_size)}")
#         uploaded_file.close()
#     return {"status": 200}


@app.errorhandler(404)
def page_not_found(error):
    return 'This page does not exist', 404
