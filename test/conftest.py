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
import os
import pytest
from ensembl.production.event.app.main import app

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry


# pytest_plugins = ["docker_compose"]

# @pytest.fixture(scope="session")
# def docker_compose_file(pytestconfig):
#     return os.path.join(str(pytestconfig.rootdir), "docker-compose-test.yml")


# @pytest.fixture(scope="module")
# def event_app_url(module_scoped_container_getter):
#     """ Wait for the event_app to become responsive """
#     request_session = requests.Session()
#     retries = Retry(total=5, backoff_factor=3, status_forcelist=[500, 502, 503, 504])
#     request_session.mount("http://", HTTPAdapter(max_retries=retries))

#     service = module_scoped_container_getter.get("event_app").network_info[0]
#     api_url = f"http://{service.hostname}:{service.host_port}"
#     return api_url



@pytest.fixture
def appclient():
    app.config['TESTING'] = True
    app.config['ES_HOST'] ='localhost'
    app.config['ES_PORT'] = '9200'
    app.config['ES_INDEX'] = 'reports_workflow'
    app.config['RELEASE'] = '105'
    app.config['EG_RELEASE'] = '52'
    app.config['RR_RELEASE'] = '24'

    with app.test_client() as appclient:
        yield appclient
        
@pytest.fixture
def event_payload():
    return {
			"src_uri": "mysql://test:test@mysql-ens-general-dev-1:3366/triticum_aestivum_jagger_core_52_105_1",
			"database": "triticum_aestivum_jagger_core_52_105_1",
			"contact": "test@ebi.ac.uk",
			"comment": "test event automation",
			"source": "Handover",
			"handover_token": "61c0c242-d282-11eb-a0d0-005056ab00f0",
			"tgt_uri": "mysql://test:test@mysql-ens-general-dev-2:3322/triticum_aestivum_jagger_core_52_105_1",
            "src_uri": "mysql://test:test@mysql-ens-general-dev-2:3322/",
			"staging_uri": "mysql://test:test@mysql-ens-general-dev-2:3322/",
			"db_division": "plants",
			"db_type": "core",
            "user": "test",
            "hive_url": "mysql://test:test@mysql-ens-general-dev-2:3322/",
			"EG_VERSION": 52,
  			"ENS_VERSION": 105,
  			"RR_VERSION": 24
    }

@pytest.fixture
def handover_payload():
    return {
			"src_uri": "mysql://test:test@mysql-ens-general-dev-1:3366/triticum_aestivum_jagger_core_52_105_1",
			"database": "triticum_aestivum_jagger_core_52_105_1",
			"contact": "test@ebi.ac.uk",
			"comment": "test event automation",
			"source": "Handover",
			"handover_token": "61c0c242-d282-11eb-a0d0-005056ab00f0",
			"tgt_uri": "mysql://test:test@mysql-ens-general-dev-2:3322/triticum_aestivum_jagger_core_52_105_1",
            "src_uri": "mysql://test:test@mysql-ens-general-dev-2:3322/",
			"staging_uri": "mysql://test:test@mysql-ens-general-dev-2:3322/",
			"db_division": "plants",
			"db_type": "core",
			"EG_VERSION": 52,
  			"ENS_VERSION": 105,
  			"RR_VERSION": 24
    }
    
@pytest.fixture
def workflow_stop_payload():
    return {
			"handover_token": "61c0c242-d282-11eb-a0d0-005056ab00f0",
            "job_id": "[ssh://localhost]-[3425.0]",
            "pipeline_name": "CoreStats"
    }   

@pytest.fixture
def workflow_restart_payload():
    return {
			"handover_token": "61c0c242-d282-11eb-a0d0-005056ab00f0",
            "restart_type": "BEEKEEPER",
    } 

@pytest.fixture
def workflow_integration_payload():
    return {
		"src_uri": "mysql://root:root@ensmysql:3306/triticum_aestivum_jagger_test_52_105_1",
		"database": "triticum_aestivum_jagger_test_52_105_1",
		"contact": "vinay@ebi.ac.uk",
		"comment": "wheat cultivars handover 105",
		"source": "Handover",
		"handover_token": "61c0c242-d282-11eb-a0d0-005056ab00f3",
		"tgt_uri": "mysql://root:root@ensmysql:3306/triticum_aestivum_jagger_test_52_105_1",
		"staging_uri": "mysql://root:root@ensmysql:3306/",
		"db_division": "test",
		"db_type": "core",
		"EG_VERSION": 52,
		"ENS_VERSION": 105,
		"RR_VERSION": 24                	
	}