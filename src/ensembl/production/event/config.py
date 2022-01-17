#!/usr/bin/env python
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
#    limitations under the License.

import os
from pathlib import Path
from ensembl.production.core.config import load_config_yaml

class config():

        config_file_path = os.environ.get('EVENT_CONFIG_PATH', os.path.join(os.path.dirname(__file__),
                                                                            'event_config.dev.yaml'))
        file_config = load_config_yaml(config_file_path)
        report_server = os.environ.get("REPORT_SERVER",
                                file_config.get('report_server', "amqp://guest:guest@ensrabbitmq:5672/"))
        report_exchange = os.environ.get("REPORT_EXCHANGE",
                                 file_config.get('report_exchange', 'event_report_exchange'))
        report_exchange_type = os.environ.get("REPORT_EXCHANGE_TYPE",
                                      file_config.get('report_exchange_type', 'topic'))                                 
        event_uri = os.environ.get("EVENT_URI",
                                   file_config.get('event_uri', 'http://event_app:5000/'))


class EventConfig(config):
        """Config For Event App """
 
        event_lookup = os.environ.get("EVENT_LOOKUP_FILE",
                              config.file_config.get('event_lookup_file', 
                              os.path.join(os.path.dirname(__file__), "./event_lookup.json")))
        process_lookup = os.environ.get("PROCESS_LOOKUP_FILE",
                                config.file_config.get('process_lookup_file', 
                                os.path.join(os.path.dirname(__file__), "./process_lookup.json")))

        #hive_url = os.environ.get("HIVE_URL",config.file_config.get('hive_url', 'mysql://test:test@mysqlhiveprod:3306/'))  
        #farm_user = os.environ.get("FARM_USER",config.file_config.get('user', 'ens'))  
        ES_HOST = os.environ.get('ES_HOST', config.file_config.get('es_host', 'elasticsearch'))
        ES_PORT = os.environ.get('ES_PORT', config.file_config.get('es_port', '9200'))
        ES_INDEX = os.environ.get('ES_INDEX', config.file_config.get('es_index', 'reports_workflow'))
        RELEASE = os.environ.get('ENS_RELEASE', config.file_config.get('ens_release', '105'))
        EG_RELEASE = os.environ.get('EG_RELEASE', config.file_config.get('eg_release', '52'))
        RR_RELEASE = os.environ.get('RR_RELEASE', config.file_config.get('rr_release', '24'))

class EventCeleryConfig(config):
        """ Config For Celery App"""

        broker_url = os.environ.get("CELERY_BROKER_URL",
                            config.file_config.get('celery_broker_url', 'pyamqp://guest:guest@ensrabbitmq:5672/'))
        result_backend = os.environ.get("CELERY_RESULT_BACKEND",
                                config.file_config.get('celery_result_backend', 'rpc://guest:guest@ensrabbitmq:5672/'))
        smtp_server = os.environ.get("SMTP_SERVER",
                             config.file_config.get('smtp_server', 'localhost'))
        from_email_address = os.environ.get("FROM_EMAIL_ADDRESS",
                                    config.file_config.get('from_email_address', 'ensembl-production@ebi.ac.uk'))
        retry_wait = int(os.environ.get("RETRY_WAIT",
                                      config. file_config.get('retry_wait', 60)))

        task_track_started=True
        result_persistent=True

        task_routes = {
                #'ensembl.event.celery.tasks': {'queue': 'event'},
                #'ensembl.event.celery.tasks.workflow_*': {'queue': 'workflow'},
                #'ensembl.event.celery.tasks.monitor_*': {'queue': 'monitor'}
        }

class PySagaConfig(config):

        NOAH = {
          'REMOTE_HOST': os.environ.get("REMOTE_HOST_NOAH", config.file_config.get("remote_host_noah", "localhost")), 
          #'ADDRESS' : os.environ.get("ADDRESS_NOAH", config.file_config.get("address_noah","10.7.95.60")),
          'ADDRESS' : os.environ.get("ADDRESS_NOAH", config.file_config.get("address_noah","localhost")),
          'USER' :  os.environ.get("USER", config.file_config.get("user","vinay")),  # vaild user in remote host 
          'PASSWORD' : os.environ.get("PASSWORD", ""),  # required only if ssh is not configured for remote user 
          'WORKING_DIR' : os.environ.get('WORKING_DIR', config.file_config.get("pwd", f"{Path.home()}/logs"))  # Your working directory to store logs and temp dirs
        }
        CODON = {
          'REMOTE_HOST': os.environ.get("REMOTE_HOST_CODON", config.file_config.get("remote_host_codon", "localhost")), 
          #'ADDRESS' : os.environ.get("ADDRESS_CODON", config.file_config.get("address_codon","10.36.17.176")),
          'ADDRESS' : os.environ.get("ADDRESS_CODON", config.file_config.get("address_codon","localhost")),
          'USER' :  os.environ.get("USER", config.file_config.get("user","root")),  # vaild user in remote host 
          'PASSWORD' : os.environ.get("PASSWORD", ""),  # required only if ssh is not configured for remote user 
          'WORKING_DIR' : os.environ.get('WORKING_DIR', config.file_config.get("pwd", f"{Path.home()}/logs"))  # Your working directory to store logs and temp dirs
        }        
        DEFAULT_HOST_DETAILS = os.environ.get("DEFAULT_HOST_DETAILS", config.file_config.get("default_host_details", "CODON"))
        FARM_USER = os.environ.get("FARM_USER",config.file_config.get('user', 'root'))
        HIVE_URL = os.environ.get("HIVE_URL", config.file_config.get("hive_url", 'mysql://root:root@ensmysql:3306/'))  # hive database string

