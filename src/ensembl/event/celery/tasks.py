'''
@author: dstaines; vinay
'''
import json
import logging
import re

from ensembl.event.celery.celery import app
from ensembl.event.client import EventClient
from ensembl.event.client import QrpClient
import ensembl.event.config as cfg

from ensembl.workflow.monitor import RemoteCmd
from ensembl.workflow.hive import construct_pipeline
from ensembl.workflow.dispatcher import WorkflowDispatcher

from ensembl.production.core.amqp_publishing import AMQPPublisher
from ensembl.production.core.reporting import make_report, ReportFormatter

from sqlalchemy.engine.url import make_url

species_pattern = re.compile(r'^(?P<prefix>\w+)_(?P<type>core|rnaseq|cdna|otherfeatures|variation|funcgen)(_\d+)?_(?P<release>\d+)_(?P<assembly>\d+)$')
compara_pattern = re.compile(r'^ensembl_compara(_(?P<division>[a-z]+|pan)(_homology)?)?(_(\d+))?(_\d+)$')
ancestral_pattern = re.compile(r'^ensembl_ancestral(_(?P<division>[a-z]+))?(_(\d+))?(_\d+)$')

event_client = EventClient(cfg.event_uri)
qrp_clinet = QrpClient(cfg.event_uri)


logger = logging.getLogger(__name__)

event_formatter = ReportFormatter('event_processing')
publisher = AMQPPublisher(cfg.report_server, cfg.report_exchange, formatter=event_formatter)


def log_and_publish(report):
    """Handy function to mimick the logger/publisher behaviour.
    """
    level = report['report_type']
    routing_key = 'report.%s' % level.lower()
    logger.log(getattr(logging, level), report['msg'])
    publisher.publish(report, routing_key)


@app.task(bind=True)
def process_result(self, event, process, job_id):
    """
    Wait for the completion of the job and then process any output further
    """

    # allow infinite retries
    self.max_retries = None
    genome = event['genome']
    checking_msg ='Checking %s event %s' % (process, job_id)
    log_and_publish(make_report('INFO', checking_msg, event, genome))
    result = event_client.retrieve_job(process, job_id)
    if (result['status'] == 'incomplete') or (result['status'] == 'running') or (result['status'] == 'submitted'):
        log_and_publish(make_report('INFO', 'Job incomplete, retrying', event, genome))
        raise self.retry()
    result_msg = 'Handling result for %s' % json.dumps(event)
    log_and_publish(make_report('DEBUG', 'Job incomplete, retrying', event, genome))
    result_dump = json.dumps(result)
    if result['status'] == 'failure':
        log_and_publish(make_report('FATAL', 'Event failed: %s' % result_dump, event, genome))
    else:
        log_and_publish(make_report('INFO', 'Event succeeded: %s' % result_dump, event, genome))
        # TODO
        # 1. update metadata
        # 2. schedule new events as required

    return event['event_id']

#Automate QRP Workflow
def parse_db_infos(database):
    """Parse database name and extract db_prefix and db_type. Also extract release and assembly for species databases"""
    if species_pattern.match(database):
        m = species_pattern.match(database)
        db_prefix = m.group('prefix')
        db_type = m.group('type')
        release = m.group('release')
        assembly = m.group('assembly')
        return db_prefix, db_type, release, assembly
    elif compara_pattern.match(database):
        m = compara_pattern.match(database)
        division = m.group('division')
        db_prefix = division if division else 'vertebrates'
        return db_prefix, 'compara', None, None
    elif ancestral_pattern.match(database):
        m = ancestral_pattern.match(database)
        division = m.group('division')
        db_prefix = division if division else 'vertebrates'
        return db_prefix, 'ancestral', None, None
    else:
        raise ValueError("Database type for" + database + " is not expected. Please contact the Production team")


def prepare_payload(spec):
    """Prepare payload to run production pipeline"""
    try:
        src_url = make_url(spec['src_uri'])
        
        (db_prefix, db_type, release, assembly) = parse_db_infos(src_url.database)
        
        workflow = WorkflowDispatcher(db_type)
        
        return workflow.create_template(spec, species='')
    except Exception as e:
        raise Exception(str(e))


def initiate_pipeline(spec, event={}, rerun=False):
     """Initiates the qrp pipelines for given payload """

     try:

         # prepare the payload with production pipelines based on dbtype and division
         spec.update(prepare_payload(spec))
         # spec = prepare_payload(spec)  
         if 'flow' not in spec:
             raise Exception('Unable to construct Flow from jina template')

         spec['job_status'] = 'inprogress'
         if rerun:
             qrp_clinet.update_record(spec)
         else:
             qrp_clinet.insert_record(spec)
         
         monitor_process_pipeline.delay(spec)
         
         return {'status': True, 'error': ''}
     except Exception as e:
         spec['status'] = False
         spec['error'] = str(e)
         qrp_clinet.update_record(spec)
         return {'status': False, 'error': str(e)} 

@app.task(bind=True)
def monitor_process_pipeline(self, spec):
     """Process the each pipeline object declared in flow"""
     try:

         if  spec.get('status', False):
             if len(spec.get('flow',[])) > 0:
                 job = spec['flow'].pop(0)
                 spec['current_job'] = job
                 spec['job_status'] = 'inprogress'
                 #pipeline_status.insert_record(spec)
                 qrp_clinet.update_record(spec)
                 qrp_run_pipeline.delay(job, spec)

             elif  len(spec.get('flow', [])) == 0:
                 spec['job_status'] = 'done'
                 spec['current_job'] = {}  
                 qrp_clinet.update_record(spec)
         else :
             spec['job_status'] = 'error'
             qrp_clinet.insert_record(spec)

     except Exception as e :
         spec['job_status'] = 'error'
         spec['error'] = str(e)
         qrp_clinet.update_record(spec)
     return True

@app.task(bind=True)
def qrp_run_pipeline(self, run_job, global_spec):
     """Celery worker  to initiate pipeline and its beekeeper"""

     try :
         temp = construct_pipeline(run_job, global_spec)
         #execute remote command over ssh 
         exece = RemoteCmd(mysql_url=temp['mysql_url'])
         global_spec['hive_db_uri'] = temp['mysql_url']
         qrp_clinet.update_record(global_spec)

         job = exece.run_job(command=' '.join(temp['init']['command']), args=temp['init']['args'],
                             stdout=temp['init']['stdout'], stderr=temp['init']['stderr'])

         if job['status']:
             #run beekeeper 
             job = exece.run_job(command=' '.join(temp['beekeeper']['command']),
                                  args=temp['beekeeper']['args'], stdout=temp['beekeeper']['stdout'], stderr=temp['beekeeper']['stderr'])
             beekeeper_status = exece.beekeper_status()
             if beekeeper_status['status'] and beekeeper_status['value'] == 'NO_WORK':
                 global_spec['status'] = True
                 global_spec['completed_jobs'].append(global_spec['current_job'])
                 global_spec['current_job'] = {}
             else:
                 global_spec['status'] = False
                 global_spec['error'] = beekeeper_status['value']
         else:
             global_spec['status'] = False
             global_spec['error'] = job['error']

         monitor_process_pipeline.delay(global_spec)
         return run_job['PipelineName'] + ' : done'

     except Exception as e:
         global_spec['status'] = False
         global_spec['error'] =  str(e)
         monitor_process_pipeline.delay(global_spec)  
         return run_job['PipelineName'] + ' : Exception error: ' + str(e)