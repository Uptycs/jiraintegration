FROM tiangolo/uwsgi-nginx-flask:latest

ENV CONFIG_FILE /app/config/config.ini
COPY ./app /app
RUN pip install -r /app/requirements.txt
