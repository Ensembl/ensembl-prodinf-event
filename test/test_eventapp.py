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
import requests
from requests.adapters import HTTPAdapter
from requests.packages.urllib3.util.retry import Retry
from requests.exceptions import ConnectionError
from marshmallow import RAISE
from ensembl.production.workflow.dispatcher import WorkflowDispatcher
from ensembl.production.event.models.schema import HandoverSpec, RestartHandoverSpec, StopHandoverSpec
import json 
import time

def is_responsive(url):
    try:
        response = requests.get(url)
        if response.status_code == 200:
            return True
    except ConnectionError:
        return False

def requests_retry_session(
    retries=5,
    backoff_factor=20,
    status_forcelist=(500, 502, 504),
    session=None,
):
    session = session or requests.Session()
    retry = Retry(
        total=retries,
        read=retries,
        connect=retries,
        backoff_factor=backoff_factor,
        status_forcelist=status_forcelist,
    )
    adapter = HTTPAdapter(max_retries=retry)
    session.mount('http://', adapter)
    return session

    
def test_invalid_handover_payload(appclient, event_payload):
    payload={}
    response = appclient.post('/workflows/submit', data=json.dumps(payload))
    assert response.status_code == 400

def test_valid_handover_payload(appclient, handover_payload):
    payload={}
    response = appclient.post('/workflows/submit', data=json.dumps(handover_payload))
    assert response.status_code == 400

def test_valid_handover_schema(appclient, handover_payload):
    handover_schema = HandoverSpec()
    assert handover_schema.loads(json_data=json.dumps(handover_payload), unknown=RAISE)

def test_valid_workflow_stop_schema(appclient, workflow_stop_payload):
    stop_schema = StopHandoverSpec()
    assert stop_schema.loads(json_data=json.dumps(workflow_stop_payload), unknown=RAISE)

def test_valid_workflow_stop_schema(appclient, workflow_restart_payload):
    restart_schema = RestartHandoverSpec()
    assert restart_schema.loads(json_data=json.dumps(workflow_restart_payload), unknown=RAISE)
    

def test_event_app_doc_status(): 
    response = requests_retry_session().get(f"http://localhost:5008/apidocs")
    assert response.status_code == 200
        
def test_submit_workflow(workflow_integration_payload):
    response = requests_retry_session().post("http://localhost:5008/workflows/submit", json=workflow_integration_payload)
    res = response.json()['spec']
    assert response.status_code == 200
    assert res['handover_token'] == workflow_integration_payload['handover_token']
    assert res['status'] == True
    assert res['database'] == workflow_integration_payload['database']
    assert bool(res['current_job']) == False
    assert len(res['flow']) == 1    
    assert len(res['completed_jobs']) == 0
    

def test_workflow_completed_status(workflow_integration_payload):
    
    timeout = time.time() + 60*15 
    response = requests_retry_session(status_forcelist=(500, 502, 504, 404, 400), backoff_factor=30).get(f"http://localhost:9200/reports_workflow")
    assert response.status_code == 200
    
    while True:
        
        response = requests_retry_session(status_forcelist=(500, 502, 504, 404, 400, 401), backoff_factor=30).get(f"http://localhost:5008/workflows/{workflow_integration_payload['handover_token']}")
        if len(response.json()) :
            spec = response.json()[0]
            if spec['params']['workflow'] != 'STARTED' or spec['report_type'] == 'ERROR':
                break
            
        if time.time() > timeout:
            break  
              
    assert len(spec['params']['flow']) == 0
    assert bool(spec['params']['current_job']) == False
    assert len(spec['params']['completed_jobs']) == 1
    assert spec['message'] == f"Workflow completed for handover {workflow_integration_payload['handover_token']}"
