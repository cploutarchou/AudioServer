FROM python:3
LABEL maintainer="Christos Ploutarchou<cploutarchou@gmail.com>"
COPY requirements.txt /tmp/
COPY scripts/app/entrypoint.sh /tmp/
RUN pip install -U pip
RUN pip install -r /tmp/requirements.txt  && pip install gunicorn
RUN chmod +x /tmp/entrypoint.sh
COPY ./app /app
CMD ["/app/uwsgi", "/app/wsgi.ini"]
WORKDIR /app
ENTRYPOINT ["/tmp/entrypoint.sh"]