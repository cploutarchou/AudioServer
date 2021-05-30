ALLOWED_EXTENSIONS = ({'mp3', 'wav', 'ogg'})


def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS
