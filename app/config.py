from dotenv import load_dotenv

import os
load_dotenv()
env_type = os.environ['ENV_TYPE']
debug = os.environ['DEBUG']
debug = True if debug == 'True' else False
if env_type is True:
    print(f"Debug Mode is on")
    load_dotenv()

# APPLICATION CONFIGURATION
secret = os.environ["SECRET_KEY"]
upload_dir = os.environ["UPLOADS_DIR"]

# MONGO DB SETTINGS
mongo_host = os.environ["MONGODB_HOST"]
mongodb_port = os.environ["MONGODB_PORT"]
mongo_db = os.environ["MONGODB_DB"]
mongo_connect = os.environ["MONGODB_CONNECT"]
mongo_connect = True if mongo_connect == 'True' else False
# EMAIL SETTINGS
email_username = os.environ["EMAIL_USERNAME"]
email_password = os.environ["EMAIL_PASSWORD"]
email_host = os.environ["EMAIL_HOST"]
email_port = os.environ["EMAIL_PORT"]
ssl_support = os.environ["EMAIL_SSL_SUPPORT"]
email_from = os.environ["EMAIL_FROM"]
ssl_support = True if ssl_support == 'True' else False
