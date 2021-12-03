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
from ensembl.production.workflow.hive import construct_pipeline

def test_workflow_for_species(event_payload):
    workflow_obj = WorkflowDispatcher('test', division='plants', species='triticum_aestivum_jagger')
    test_workflow = workflow_obj.create_template(event_payload, division='plants', species='triticum_aestivum_jagger')  
    assert test_workflow['status'] == True
    assert len(test_workflow['flow']) == 1
    assert len(test_workflow['completed_jobs']) == 0
    pipeline_params = test_workflow['flow'][0]['PipeParams']['params']
    assert pipeline_params['-species'] == 'triticum_aestivum_jagger'
    assert pipeline_params['-division'] == 'plants'
    assert pipeline_params['-pipeline_name'] == 'test_rr_core_stats_triticum_aestivum_jagger_105'

def test_workflow_pipeline_cmd(event_payload):
    workflow_obj = WorkflowDispatcher('test', division='plants', species='triticum_aestivum_jagger')
    test_workflow = workflow_obj.create_template(event_payload, division='plants', species='triticum_aestivum_jagger')  
    test_workflow.update(event_payload) 
    current_job = test_workflow['flow'][0]
    cmd = construct_pipeline(current_job, test_workflow)
    assert cmd['HOST'] == 'TEST'
    assert cmd['mysql_url'] == f"{event_payload['hive_url']}test_test_rr_core_stats_triticum_aestivum_jagger_105"
    assert all( i in cmd for i in ['init', 'beekeeper', 'mysql_url', 'HOST'] )