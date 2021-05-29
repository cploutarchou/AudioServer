from dotenv import load_dotenv

import os

load_dotenv()
# Email setting
email_username = os.getenv("EMAIL_USERNAME", None)
email_password = os.getenv("EMAIL_PASSWORD", None)
email_host = os.getenv("EMAIL_HOST", None)
email_port = os.getenv("EMAIL_PORT", None)
ssl_support = os.getenv("EMAIL_SSL_SUPPORT", False)