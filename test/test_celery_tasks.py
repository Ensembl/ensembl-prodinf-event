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


