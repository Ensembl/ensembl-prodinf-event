import pytest
import requests

from requests.exceptions import ConnectionError
from marshmallow import RAISE
from ensembl.production.workflow.dispatcher import WorkflowDispatcher
from ensembl.production.event.models.schema import HandoverSpec, RestartHandoverSpec, StopHandoverSpec
import json 

def is_responsive(url):
    try:
        response = requests.get(url)
        if response.status_code == 200:
            return True
    except ConnectionError:
        return False

    
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
    
 
@pytest.fixture(scope="session")
def http_service(docker_ip, docker_services):
    """Ensure that HTTP service is up and responsive."""

    # `port_for` takes a container port and returns the corresponding host port
    port = docker_services.port_for("event_app", 5000)
    url = "http://{}:{}".format(docker_ip, port)
    docker_services.wait_until_responsive(
        timeout=30.0, pause=0.1, check=lambda: is_responsive(url)
    )
    return url

# def test_status_code(http_service):
#     status = 200
#     response = requests.get(http_service)

#     assert response.status_code == status