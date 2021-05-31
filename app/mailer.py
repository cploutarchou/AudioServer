from flask import render_template
from config import *

import smtplib

from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText


class Mailer:
    def __init__(self):
        self.connected = False
        self.host = email_host
        self.port = email_port
        self.username = email_username
        self.password = email_password
        self.server = None
        self.to = None
        self._from = email_from
        self.msg = None

    def set_email(self, **kwargs):
        mandatory_args = ["subject", "content", "content_type"]
        for x in mandatory_args:
            if not kwargs.get(x, False):
                raise ValueError("%s is mandatory" % (x))

        self.msg = MIMEMultipart('alternative')
        self.msg['Subject'] = kwargs['subject']

        content = MIMEText(kwargs['content'], kwargs['content_type'])
        self.msg.attach(content)

    def connect(self):
        try:
            self.server = smtplib.SMTP(self.host, self.port)
            self.server.login(self.username, self.password)
        except smtplib.SMTPConnectError as e:
            raise e
        self.connected = True

    def disconnect(self):
        try:
            self.server.quit()
        except smtplib.SMTPException as e:
            raise Exception(f"Something went wrong Unable to disconnect. Error {e}")

    def send_html_mail(self, **kwargs):
        kwargs['content_type'] = "html"
        return self.set_email(**kwargs)

    def send_text_mail(self, **kwargs):
        kwargs['content_type'] = "plain"
        return self.set_email(**kwargs)

    def set_to(self, to: list):
        if len(to) == 0:
            raise Exception("No valid Send to content. List length is zero")

        self.to = ', '.join(to)

    def send(self):
        self.connect()
        msg = self.msg
        print(self.to)
        if type(self.to) == str and self.to != "":
            msg['To'] = self.to
        else:
            raise Exception("Unable to send email. No valid recipients")

        if self._from is not None:
            msg['From'] = self._from
        else:
            raise Exception("Unable to send email. No valid From address")

        self.server.sendmail(msg['From'], msg['To'], msg.as_string())
        self.disconnect()
        return True

    def verify(self, url):
        content = render_template('verify.html', url=url)
        self.set_email(content=content, subject="Account Verification", content_type="html")
        self.send()
