#Base Docker image with uWSGI and Nginx for Flask applications in Python running in a single container
FROM tiangolo/uwsgi-nginx:python3.6
#Add a label
LABEL maintainer="cploutarchou@gmail.com"
#By default, the application runs on port 80, you can choose a different port by uncommenting the LISTEN PORT and EXPOSE
#ENV LISTEN_PORT 8080

#EXPOSE 8080
RUN pip install flask
# URL under which static (not modified by Python) files will be requested
# They will be served by Nginx directly, without being handled by uWSGI
ENV STATIC_URL /static
# Absolute path in where the static files wil be
ENV STATIC_PATH /app/static
# If STATIC_INDEX is 1, serve / with /static/index.html directly (or the static URL configured in this case it will be 0)
# ENV STATIC_INDEX 1
ENV STATIC_INDEX 0
# Add app
#COPY app /app

#RUN python3 -m ensurepip --default-pip
#RUN python -m pip install --upgrade pip setuptools wheel
#RUN pip install --no-cache-dir -r requirements.txt
# Make /app/* available to be imported by Python globally to better support several use cases like Alembic migrations.
ENV PYTHONPATH=/app
## Move the base entrypoint to reuse it
#RUN mv /entrypoint.sh /uwsgi-nginx-entrypoint.sh
## Copy the entrypoint that will generate Nginx additional configs
#COPY scripts/app/entrypoint.sh /entrypoint.sh
#RUN chmod +x /entrypoint.sh
#ENTRYPOINT ["/entrypoint.sh"]
## Run the start script provided by the parent image tiangolo/uwsgi-nginx which in turn will start Nginx and uWSGI
#CMD ["/start.sh"]

# copy over our requirements.txt file
COPY requirements.txt /tmp/

# upgrade pip and install required python packages
RUN pip install -U pip
RUN pip install -r /tmp/requirements.txt

# copy over our app code
COPY ./app /app
WORKDIR /app