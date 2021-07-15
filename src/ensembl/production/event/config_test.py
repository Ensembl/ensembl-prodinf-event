'''
@author: dstaines; Vinay Kaikala
'''
import os
from ensembl.production.core.config import load_config_yaml

class config():

        config_file_path = os.environ.get('EVENT_CONFIG_PATH')
        file_config = load_config_yaml(config_file_path)
        report_server = os.environ.get("REPORT_SERVER",
                                file_config.get('report_server', "amqp://qrp:arp@hx-cluster:31772/qrp"))
        report_exchange = os.environ.get("REPORT_EXCHANGE",
                                 file_config.get('report_exchange', 'report_exchange'))
                                 
        report_exchange_type = os.environ.get("REPORT_EXCHANGE_TYPE",
                                      file_config.get('report_exchange_type', 'direct'))                                 
        #event_uri = os.environ.get("EVENT_URI",
        #                           file_config.get('event_uri', 'http://production:5000/'))

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

        ES_HOST = os.environ.get('ES_HOST', config.file_config.get('es_host', 'hx-cluster'))
        ES_PORT = os.environ.get('ES_PORT', config.file_config.get('es_port', '31275'))
        RELEASE = os.environ.get('ENS_RELEASE', config.file_config.get('ens_release', '102'))

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
                                
        task_routes = {
                'ensembl.production.event.workflow_class.task.*' : {'queue': 'qrp'},
                'ensembl.event.celery.tasks': {'queue': 'event'},
                'ensembl.event.celery.tasks.qrp_*': {'queue': 'qrp'},
                'ensembl.event.celery.tasks.monitor_*': {'queue': 'monitor'}
        }
