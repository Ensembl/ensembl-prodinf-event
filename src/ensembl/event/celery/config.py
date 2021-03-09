import os
from ensembl.production.core.config import load_config_yaml

config_file_path = os.environ.get('EVENT_CELERY_CONFIG_PATH')
file_config = load_config_yaml(config_file_path)

broker_url = os.environ.get("CELERY_BROKER_URL",
                            file_config.get('celery_broker_url', 'pyamqp://qrp:qrp@hx-cluster:31772/qrp'))
result_backend = os.environ.get("CELERY_RESULT_BACKEND",
                                file_config.get('celery_result_backend', 'rpc://qrp:qrp@hx-cluster:31772/qrp'))
smtp_server = os.environ.get("SMTP_SERVER",
                             file_config.get('smtp_server', 'localhost'))
from_email_address = os.environ.get("FROM_EMAIL_ADDRESS",
                                    file_config.get('from_email_address', 'ensembl-production@ebi.ac.uk'))
retry_wait = int(os.environ.get("RETRY_WAIT",
                                file_config.get('retry_wait', 60)))

task_routes = {
  'ensembl.event.celery.tasks': {'queue': 'event'},
  'ensembl.event.celery.tasks.qrp_*': {'queue': 'qrp'},
  'ensembl.event.celery.tasks.monitor_*': {'queue': 'monitor'}
}
