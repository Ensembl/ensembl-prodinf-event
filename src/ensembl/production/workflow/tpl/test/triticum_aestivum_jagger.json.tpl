{% extends "base.json.tpl" %}

{% block flow %}
    {% block coreStats %}
        {
            "HOST": "TEST",
            "PipelineName": "CoreStats",
            "PipeConfig": "Bio::EnsEMBL::Production::Pipeline::PipeConfig::CoreStatistics_conf",
            "PipeParams": {
                "params": {
		         "-registry": "$REG_PROD_DIR/st5-w.pm ",	
                 {{ pipe_param('species', species) }} ,
                 {{ pipe_param('division', division)  }} ,
                 "-antispecies": "sars_cov_2" ,
                 "-pipeline_name": "test_rr_core_stats_{{ species }}_{{ spec['ENS_VERSION'] }}" ,
                 "-history_file": "$PROD_DIR/datachecks/history/st5.json"
                }, 
                "arguments":[],
                "environ":{
                    "ENS_VERSION": "{{ spec['ENS_VERSION'] }}"
                }
            }
        }
    {% endblock coreStats %}
{% endblock flow %}
