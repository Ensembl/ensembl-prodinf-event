import os
import pytest
from ensembl.production.event.app.main import app


@pytest.fixture(scope="session")
def docker_compose_file(pytestconfig):
    return os.path.join(str(pytestconfig.rootdir), "docker-compose.yml")

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