'''
@author: dstaines; Vinay Kaikala
'''
import os
from ensembl.production.core.config import load_config_yaml


config_file_path = os.environ.get('EVENT_CONFIG_PATH')
file_config = load_config_yaml(config_file_path)

event_lookup = os.environ.get("EVENT_LOOKUP_FILE",
                              file_config.get('event_lookup_file', 
                              os.path.join(os.path.dirname(__file__), "./event_lookup.json")))
process_lookup = os.environ.get("PROCESS_LOOKUP_FILE",
                                file_config.get('process_lookup_file', 
                                os.path.join(os.path.dirname(__file__), "./process_lookup.json")))
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


ES_HOST = os.environ.get('ES_HOST', file_config.get('es_host', 'hx-cluster'))
ES_PORT = os.environ.get('ES_PORT', file_config.get('es_port', '31275'))
RELEASE = os.environ.get('ENS_RELEASE', file_config.get('ens_release', '102'))
