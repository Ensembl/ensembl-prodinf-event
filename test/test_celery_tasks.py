import pytest
from ensembl.production.workflow.dispatcher import WorkflowDispatcher
from ensembl.production.event.celery_app import tasks

def test_workflow_status(event_payload):
    workflow_obj = WorkflowDispatcher('test', division='plants', species='triticum_aestivum_jagger')
    test_workflow = workflow_obj.create_template(event_payload, division='plants', species='triticum_aestivum_jagger')  
    pipeline_params = test_workflow['flow'][0]['PipeParams']['params']
    assert test_workflow['status'] == True
 
def test_parse_db_info():
    db_name = "triticum_aestivum_jagger_core_52_105_1"
    db_prefix, db_type, release, assembly = tasks.parse_db_infos(db_name)
    assert db_type == 'core'
    assert release == '105'


def test_update_workflow_status(event_payload):
    workflow_obj = WorkflowDispatcher('test', division='plants', species='triticum_aestivum_jagger')
    test_workflow = workflow_obj.create_template(event_payload, division='plants', species='triticum_aestivum_jagger')
    test_workflow = tasks.update_workflow_status(test_workflow, False, 'Canceled for test', 'Canceled')
    assert test_workflow['status'] == False
    assert test_workflow['error'] == 'Canceled for test'
    assert test_workflow['workflow'] == 'Canceled'

