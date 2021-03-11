FROM python:3.7.10
WORKDIR /app

#copy event app
COPY . /app

#Install datacheck app dependencies
RUN pip install -r requirements.txt
RUN pip install .


EXPOSE 5000
CMD  ["/usr/local/bin/gunicorn", "--config", "/app/gunicorn_config.py", "-b", "0.0.0.0:5000", "ensembl.production.event.app.main:app"]

