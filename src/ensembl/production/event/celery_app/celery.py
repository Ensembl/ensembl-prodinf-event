import logging

from celery import Celery

app = Celery('ensembl_event',
             include=['ensembl.production.event.celery.tasks'])

# Load the externalised config module from PYTHONPATH
try:
    from ensembl.production.event.config import EventCeleryConfig as celery_config
    app.config_from_object(celery_config)
except ImportError:
    logging.warning('Celery email requires event_celery_app_config module')


if __name__ == '__main__':
    app.start()
