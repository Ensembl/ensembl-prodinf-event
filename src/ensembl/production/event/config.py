'''
@author: dstaines; Vinay Kaikala
'''
import os
from ensembl.production.core.config import load_config_yaml

class config():

        config_file_path = os.environ.get('EVENT_CONFIG_PATH', os.path.join(os.path.dirname(__file__),
                                                                            'event_config.dev.yaml'))
        file_config = load_config_yaml(config_file_path)
        report_server = os.environ.get("REPORT_SERVER",
                                file_config.get('report_server', "amqp://guest:guest@localhost:5672/"))
        report_exchange = os.environ.get("REPORT_EXCHANGE",
                                 file_config.get('report_exchange', 'event_report_exchange'))
        report_exchange_type = os.environ.get("REPORT_EXCHANGE_TYPE",
                                      file_config.get('report_exchange_type', 'topic'))                                 
        event_uri = os.environ.get("EVENT_URI",
                                   file_config.get('event_uri', 'http://localhost:5000/'))


class EventConfig(config):
        """Config For Event App """
 
        event_lookup = os.environ.get("EVENT_LOOKUP_FILE",
                              config.file_config.get('event_lookup_file', 
                              os.path.join(os.path.dirname(__file__), "./event_lookup.json")))
        process_lookup = os.environ.get("PROCESS_LOOKUP_FILE",
                                config.file_config.get('process_lookup_file', 
                                os.path.join(os.path.dirname(__file__), "./process_lookup.json")))

        # hive_url = os.environ.get("HIVE_URL",config.file_config.get('hive_url', ''))  
        # farm_user = os.environ.get("FARM_USER",config.file_config.get('user', ''))  
        ES_HOST = os.environ.get('ES_HOST', config.file_config.get('es_host', ''))
        ES_PORT = os.environ.get('ES_PORT', config.file_config.get('es_port', ''))
        ES_INDEX = os.environ.get('ES_INDEX', config.file_config.get('es_index', 'reports_workflow'))
        RELEASE = os.environ.get('ENS_RELEASE', config.file_config.get('ens_release', '105'))
        EG_RELEASE = os.environ.get('EG_RELEASE', config.file_config.get('eg_release', '52'))
        RR_RELEASE = os.environ.get('RR_RELEASE', config.file_config.get('rr_release', '24'))

class EventCeleryConfig(config):
        """ Config For Celery App"""

        broker_url = os.environ.get("CELERY_BROKER_URL",
                            config.file_config.get('celery_broker_url', 'pyamqp://guest:guest@localhost:5672/'))
        result_backend = os.environ.get("CELERY_RESULT_BACKEND",
                                config.file_config.get('celery_result_backend', 'rpc://guest:guest@localhost:5672/'))
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
          'REMOTE_HOST': os.environ.get("REMOTE_HOST_NOAH", config.file_config.get("remote_host_noah", "")), 
          'ADDRESS' : os.environ.get("ADDRESS_NOAH", config.file_config.get("address_noah","")),
          'USER' :  os.environ.get("USER", config.file_config.get("user","vinay")),  # vaild user in remote host 
          'PASSWORD' : os.environ.get("PASSWORD", ""),  # required only if ssh is not configured for remote user 
          'WORKING_DIR' : os.environ.get('WORKING_DIR', config.file_config.get("pwd", "/homes/vinay/new_rapid_test"))  # Your working directory to store logs and temp dirs
        }
        CODON = {
          'REMOTE_HOST': os.environ.get("REMOTE_HOST_CODON", config.file_config.get("remote_host_codon", "")), 
          'ADDRESS' : os.environ.get("ADDRESS_NOAH", config.file_config.get("address_noah","")),
          'USER' :  os.environ.get("USER", config.file_config.get("user","vinay")),  # vaild user in remote host 
          'PASSWORD' : os.environ.get("PASSWORD", ""),  # required only if ssh is not configured for remote user 
          'WORKING_DIR' : os.environ.get('WORKING_DIR', config.file_config.get("pwd", "/homes/vinay/new_rapid_test"))  # Your working directory to store logs and temp dirs
        }        
        DEFAULT_HOST_DETAILS = os.environ.get("DEFAULT_HOST_DETAILS", config.file_config.get("default_host_details", ""))
        FARM_USER = os.environ.get("FARM_USER",config.file_config.get('user', 'vinay'))
        HIVE_URL = os.environ.get("HIVE_URL", config.file_config.get("hive_url", ''))  # hive database string

