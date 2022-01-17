{% extends "base.json.tpl" %}

{% block flow %}
    {% block eventtest %}
        {
            "HOST": "CODON",
            "TEST": "TRUE",
            "PipelineName": "TestEvent",
            "PipeConfig": "Bio::EnsEMBL::Production::Pipeline::PipeConfig::TestEvent_conf",
            "PipeParams": {
                "params": {
                    "-pipeline_name": "test_rr_test_event_{{ species }}_{{ spec['ENS_VERSION'] }}",
                    {{ pipe_param('species', species) }},
                    {{ pipe_param('division', division)  }}  
                }, 
                "arguments":[],
                "environ":{
                }
            }
        }
    {% endblock eventtest %}
{% endblock flow %}
