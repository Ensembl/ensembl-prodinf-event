# README
EnsEMBL - Production Event Service Application
========

The Event app provides a simple endpoint to submit a workflow to run ensembl production pipelines 

Implementation
==============

The `event app <./src/ensembl/event/app/main.py>`_ is a simple Flask app which defines endpoints for event. After starting the app, full API documentation is available from ``/apidocs``.

The submission of a event workflow triggers the submission of a `celery <https://github.com/Ensembl/ensembl-prodinf-envent/blob/master/docs/celery.rst>`_ task which runs series of production pipelines.

Installation
============

First clone this repo
```
  git clone https://github.com/Ensembl/ensembl-prodinf-event
  cd ensembl-prodinf-event
```
To install Python requirements using pip:


``` 
  pip install -r requirements.txt
  pip install . 
  event_api (for devlopment perpous)    
```

Configuration
=============

Configuration is minimal and restricted to the contents of `config.py <./src/ensembl/event/config.py>`_ which is restricted solely to basic Flask properties.

Running
=======

To start the main application as a standalone Flask application:

```
  export FLASK_APP=ensembl.production.event.app.main.py
  flask run --port 5000 --host 0.0.0.0
```
or to start the main application as a standalone using gunicorn with 4 threads:

```
  gunicorn -w 4 -b 0.0.0.0:5003 ensembl.production.event.app.main:app
```
Note that for production, a different deployment option should be used as the standalone flask app can only serve one request at a time.

There are multiple options, described at:
```
* http://flask.pocoo.org/docs/0.12/deploying/wsgi-standalone/
* http://flask.pocoo.org/docs/0.12/deploying/uwsgi/
```
To use a standalone gunicorn server with 4 worker threads:

```
  gunicorn -w 4 -b 0.0.0.0:5001 event_app:app
```
Running Celery
==============
The Celery task manager is used run the production pipeline as a workflow. The default backend in ``config.py`` is RabbitMQ. This can be installed as per <https://www.rabbitmq.com/>.

 Start a celery worker to run production pipeline listen to que workflow:

```
    celery -A ensembl.production.event.celery.tasks worker -l info -Q workflow -n workflow-process@%%h
```

Start a celery worker to monitor the status of pipeline listen to que monitor: 
```
    celery -A ensembl.production.event.celery.tasks worker -l info -Q monitor -n workflow-monitor@%%h
```

Build Docker Image 
==================
```
sudo docker build -t event . 
```
RUN Docker Container
====================
```
sudo docker run -p 5000:5000 -it  event:latest
```




