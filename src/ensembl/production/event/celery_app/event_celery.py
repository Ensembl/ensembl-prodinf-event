# .. See the NOTICE file distributed with this work for additional information
#    regarding copyright ownership.
#    Licensed under the Apache License, Version 2.0 (the "License");
#    you may not use this file except in compliance with the License.
#    You may obtain a copy of the License at
#        http://www.apache.org/licenses/LICENSE-2.0
#    Unless required by applicable law or agreed to in writing, software
#    distributed under the License is distributed on an "AS IS" BASIS,
#    WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#    See the License for the specific language governing permissions and
#    limitations under the License.import logging

from celery import Celery

app = Celery('ensembl_event', include=['ensembl.production.event.celery_app.tasks'])

# Load the externalised config module from PYTHONPATH
try:
    from ensembl.production.event.config import EventCeleryConfig as celery_config
    app.config_from_object(celery_config)

except ImportError:
    logging.warning('Celery email requires event_celery_app_config module')


if __name__ == '__main__':
    app.start()
