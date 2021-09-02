'''
@author: dstaines; vinay
'''
import json
import logging
import re
import time

from ensembl.production.event.celery_app.event_celery import app
from celery import states
from celery.result import AsyncResult
#from celery.task.control import revoke

from ensembl.production.event.client import EventClient
#from ensembl.production.event.client import QrpClient
from ensembl.production.event.config import EventConfig as cfg
from ensembl.production.event.config import PySagaConfig as pycfg

from ensembl.production.workflow.monitor import RemoteCmd
from ensembl.production.workflow.hive import construct_pipeline
from ensembl.production.workflow.dispatcher import WorkflowDispatcher

from ensembl.production.core.amqp_publishing import AMQPPublisher
from ensembl.production.core.reporting import make_report, ReportFormatter

from sqlalchemy.engine.url import make_url
import radical.saga as saga

species_pattern = re.compile(r'^(?P<prefix>\w+)_(?P<type>core|rnaseq|cdna|otherfeatures|variation|funcgen)(_\d+)?_(?P<release>\d+)_(?P<assembly>\d+)$')
compara_pattern = re.compile(r'^ensembl_compara(_(?P<division>[a-z]+|pan)(_homology)?)?(_(\d+))?(_\d+)$')
ancestral_pattern = re.compile(r'^ensembl_ancestral(_(?P<division>[a-z]+))?(_(\d+))?(_\d+)$')

event_client = EventClient(cfg.event_uri)
#qrp_clinet = QrpClient(cfg.event_uri)


logger = logging.getLogger(__name__)

event_formatter = ReportFormatter('event_processing')
publisher = AMQPPublisher(cfg.report_server, 
                          cfg.report_exchange,
                          exchange_type=cfg.report_exchange_type,  
                          formatter=event_formatter)


def log_and_publish(report):
    """Handy function to mimick the logger/publisher behaviour.
    """
    level = report['report_type']
    routing_key = 'report.%s' % level.lower()
    logger.log(getattr(logging, level), report['msg'])
    publisher.publish(report, routing_key)


# @app.task(bind=True)
# def process_result(self, event, process, job_id):
#     """
#     Wait for the completion of the job and then process any output further
#     """

#     # allow infinite retries
#     self.max_retries = None
#     genome = event['genome']
#     checking_msg ='Checking %s event %s' % (process, job_id)
#     log_and_publish(make_report('INFO', checking_msg, event, genome))
#     result = event_client.retrieve_job(process, job_id)
#     if (result['status'] == 'incomplete') or (result['status'] == 'running') or (result['status'] == 'submitted'):
#         log_and_publish(make_report('INFO', 'Job incomplete, retrying', event, genome))
#         raise self.retry()
#     result_msg = 'Handling result for %s' % json.dumps(event)
#     log_and_publish(make_report('DEBUG', 'Job incomplete, retrying', event, genome))
#     result_dump = json.dumps(result)
#     if result['status'] == 'failure':
#         log_and_publish(make_report('FATAL', 'Event failed: %s' % result_dump, event, genome))
#     else:
#         log_and_publish(make_report('INFO', 'Event succeeded: %s' % result_dump, event, genome))
#         # TODO
#         # 1. update metadata
#         # 2. schedule new events as required

#     return event['event_id']

#Automate QRP Workflow

def update_workflow_status(spec, status, error, workflow):
    "Update workflow status "

    spec['status'] = status
    spec['error'] = error
    spec['workflow'] = workflow

    return spec


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
        (species_name, db_type, release, assembly) = parse_db_infos(src_url.database)       
        workflow = WorkflowDispatcher(db_type) 
        return workflow.create_template(spec, species=species_name)
    except Exception as e:
        raise Exception(str(e))
 

def stop_running_job(job_id, spec):
    "Stop radical saga job using job_id"
    try:
        
        event_job = RemoteCmd(
            REMOTE_HOST = pycfg.REMOTE_HOST,
            ADDRESS = pycfg.ADDRESS,  
            USER = pycfg.USER,
            PASSWORD = pycfg.PASSWORD, 
            WORKING_DIR = pycfg.WORKING_DIR
            )
        terminate_status = event_job.job_status(job_id, stop_job=True)
        if terminate_status['status']:
            update_workflow_status(spec, status=False, error='', workflow=saga.job.CANCELED)
            msg= f"Workflow Canceled for handover {spec['handover_token']}"
            log_and_publish(make_report('INFO', msg, spec))
            # stop all running beekeeper jobs  

        return terminate_status    
    except Exception as e:
        raise Exception(str(e))  
    

def restart_workflow(restart_type, spec):
    "Restart the Workflow"

    try:

        update_workflow_status(spec, status=True, error='', workflow=states.STARTED)    

        if restart_type == 'BEEKEEPER':
            current_job = spec['current_job']
            #set param init_pipeline to False to run beekeeper alone 
            log_and_publish(make_report('INFO', f"RESTART {current_job['PipelineName']} Pipeline", spec))
            workflow_run_pipeline.delay(current_job, spec, init_pipeline=False)  

        elif restart_type == 'INIT_PIPELINE':
            current_job = spec['current_job']
            log_and_publish(make_report('INFO', f"RESTART {current_job['PipelineName']} Pipeline", spec))
            workflow_run_pipeline.delay(current_job, spec)

        elif restart_type == 'SKIP_CURRENT_PIPELINE':
            current_job = spec['current_job']
            #set current job status to skipped for reference
            current_job['pipeline_status'] = 'SKIPPED'
            spec['completed_jobs'].append(current_job)
            log_and_publish(make_report('INFO', f"SKIPPED {current_job['PipelineName']} Pipeline", spec))
            monitor_process_pipeline.delay(spec)

        elif restart_type == 'WORKFLOW':
            current_job = [ spec['current_job'] ]
            spec['flow'] = spec['completed_jobs'] + current_job + spec['flow']
            #reset the currentjob and completed job to null
            spec['current_job'] ={}
            spec['completed_jobs']=[]
            log_and_publish(make_report('INFO', 'Restart Entire Workflow', spec))
            workflow_run_pipeline.delay(current_job, spec)

        return True
    except Exception as e:
        raise Exception(str(e))    


@app.task(bind=True, queue="event_job_status", default_retry_delay=120, max_retries=None)
def event_job_status(self, spec, job_id):
    try:
        event_job_status = RemoteCmd(
        REMOTE_HOST = pycfg.REMOTE_HOST,
        ADDRESS = pycfg.ADDRESS,  
        USER = pycfg.USER,
        PASSWORD = pycfg.PASSWORD, 
        WORKING_DIR = pycfg.WORKING_DIR
        )
        event_status = event_job_status.job_status(job_id)
        if event_status['status']: 
        
            if  event_status['job_status'] in [saga.job.DONE]:                          
                #check if beekeeper is completed successfully
                beekeeper_status = event_job_status.beekeper_status(spec['hive_db_uri']) 
                if beekeeper_status['status'] and beekeeper_status['value'] == 'NO_WORK':
                    msg= f"Pipeline {spec['current_job']['PipelineName']} {saga.job.DONE} "
                    spec['status'] = True
                    spec['completed_jobs'].append(spec['current_job'])
                    spec['current_job']={}
                    log_and_publish(make_report('INFO', msg, spec)) 
                    #start another pipeline  
                    monitor_process_pipeline.delay(spec)
                else:
                    msg= f"Pipeline {spec['current_job']['PipelineName']} beekeeper failed {beekeeper_status['error']}"
                    update_workflow_status(spec, status=False, error=beekeeper_status['value'], workflow=saga.job.FAILED) 
                    log_and_publish(make_report('ERROR', msg, spec))
                
            if event_status['job_status'] in [ saga.job.SUSPENDED, saga.job.CANCELED, saga.job.FAILED, saga.job.UNKNOWN]:
                msg= f"Pipeline {spec['current_job']['PipelineName']} {event_status['job_status']}"
                update_workflow_status(spec, status=False, error=event_status['error'], workflow=event_status['error'])
                log_and_publish(make_report('ERROR', msg, spec)) 
                return False 
             
        else:
            msg = f"Failed to fetch Pipeline {spec['current_job']['PipelineName']}  status "
            update_workflow_status(spec, status=False, error=event_status['error'] , workflow=saga.job.FAILED)       
            log_and_publish(make_report('ERROR', msg, spec))  
            return False

    except Exception as e:    
        update_workflow_status(spec, status=False, error=str(e) , workflow=saga.job.FAILED)
        log_and_publish(make_report('ERROR', str(e), spec))       
        return False
    
    if event_status['status']: 
        if  event_status['job_status'] in [saga.job.PENDING, saga.job.RUNNING] :
            msg = f"Pipeline {spec['current_job']['PipelineName']} {saga.job.RUNNING}"
            spec_debug = {key: value for (key, value) in spec.items() if key not in ['flow', 'completed_jobs'] }
            log_and_publish(make_report('DEBUG', msg, spec_debug))
            raise self.retry()
    
    return msg     

@app.task(bind=True, queue="workflow",  task_track_started=True,
                            result_persistent=True)

def workflow_run_pipeline(self, run_job, global_spec, init_pipeline=True):
     """Celery worker to initiate pipeline and its beekeeper"""

     try :
        temp = construct_pipeline(run_job, global_spec)
        #execute remote command over ssh 
        exece = RemoteCmd(
            REMOTE_HOST = pycfg.REMOTE_HOST,
            ADDRESS = pycfg.ADDRESS,  
            USER = pycfg.USER,
            PASSWORD = pycfg.PASSWORD, 
            WORKING_DIR = pycfg.WORKING_DIR,
            mysql_url=temp['mysql_url']
            )
        global_spec['task_id'] =  self.request.id   
        global_spec['hive_db_uri'] = temp['mysql_url']
        msg = f"Pipeline {run_job['PipelineName']} Intiated"
        log_and_publish(make_report('DEBUG', msg, global_spec))

        job = { 'status' : True }

        if init_pipeline:
        
            job = exece.run_job(command=' '.join(temp['init']['command']), args=temp['init']['args'],
                           stdout=temp['init']['stdout'], stderr=temp['init']['stderr'], synchronus=True)
        
        if job['status']:

            job = exece.run_job(command=  ' '.join(temp['beekeeper']['command']),
                               args=temp['beekeeper']['args'], stdout=temp['beekeeper']['stdout'], stderr=temp['beekeeper']['stderr'])

            if job['status'] :

                global_spec['current_job']['job_id'] = job['job_id']
                msg = f"Pipeline {run_job['PipelineName']} {job['state']}"
                log_and_publish(make_report('INFO', msg, global_spec))
                event_job_status.delay(global_spec, job['job_id'])                  
            else:
                raise ValueError(f"Pipeline {run_job['PipelineName']} failed : {job['error']}")
        else:
            raise ValueError(f"Pipeline {run_job['PipelineName']} failed: {job['error']}")  
       
        return True

     except Exception as e:
        update_workflow_status(global_spec, status=False, error=str(e) , workflow=saga.job.FAILED)
        log_and_publish(make_report('ERROR', str(e), global_spec))        
        return f"{run_job['PipelineName']} : Exception error:  {str(e)}"

@app.task(bind=True, queue="monitor")
def monitor_process_pipeline(self, spec):
    print('my work flow')
    try:

        if  spec.get('status', False):
            if len(spec.get('flow',[])) > 0:
                job = spec['flow'].pop(0)
                spec['current_job'] = job
                spec['status'] = True
                spec['workflow'] = states.STARTED
                msg= f"Pipeline {job['PipelineName']} Started!"
                log_and_publish(make_report('INFO', msg, spec))
                #run pipeline job
                workflow_run_pipeline.delay(job, spec)
    
            elif len(spec.get('flow', [])) == 0:
                spec['status'] = True
                spec['current_job'] = {}  
                spec['workflow'] = saga.job.DONE
                msg= f"Workflow completed for handover {spec['handover_token']}"
                log_and_publish(make_report('INFO', msg, spec))
        else :
            spec['status'] = False
            spec['workflow'] = saga.job.FAILED
            msg= f"Workflow failed to complete for handover {spec['handover_token']}"
            log_and_publish(make_report('ERROR', msg, spec))
             
    except Exception as e :
        update_workflow_status(spec, status=False, error=str(e) , workflow=saga.job.FAILED)
        msg= f"Workflow failed to complete for handover {spec['handover_token']}: {str(e)}"
        log_and_publish(make_report('ERROR', msg, spec))
        return f"Error:  {str(e)}"
        
    return True


def initiate_pipeline(spec, event={}, rerun=False):
    """Initiates the qrp pipelines for given payload """

    try:
        # prepare the payload with production pipelines based on dbtype and division
        spec.update(prepare_payload(spec)) 
        #set username to run the pipeline 
        if not spec.get('user', None):
            spec['user']=cfg.farm_user
        #set hive url to run the pipelines
        if not spec.get('hive_url', None): 
            spec['hive_url']=cfg.hive_url

        if 'flow' not in spec or len(spec['flow']) == 0:
            raise Exception('Unable to construct workflow to run production pipeline.')

        #remove .....
        #spec['flow'] = [spec['flow'][0]]
        msg = f"Workflow Started for handover token {spec['handover_token']}"
        log_and_publish(make_report('INFO', msg, spec))

        #submit workflow to monitor queue   
        monitor_process_pipeline.delay(spec)
        
        return {'status': True, 'error': '' , 'spec': spec}

    except Exception as e:
        update_workflow_status(spec, status=False, error=str(e) , workflow=saga.job.FAILED)
        msg = f"Workflow failed for handover token {spec['handover_token']}"
        log_and_publish(make_report('INFO', msg, spec))
        return {'status': False, 'error': str(e), 'spec': spec} 

