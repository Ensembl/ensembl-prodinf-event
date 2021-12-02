{% extends "base.json.tpl" %}

{% set NEXT_RELEASE_VERSION = spec['ENS_VERSION'] + 1 %}

{% block flow %}
    {% block updatePackedStatus %}
        {
            "HOST": "CODON",
            "PipelineName": "updatePackedStatus",
            "PipeConfig": "Bio::EnsEMBL::Production::Pipeline::PipeConfig::UpdatePackedStatus_conf",
            "PipeParams": {
                "params": {
                    "-registry": "$REG_PROD_DIR/st5-w.pm ",
                    "EMPTY": "$(meta1-w details script_metadata_)",
                    {{ pipe_param('species', species) }},
                    "-pipeline_name": "pack_status_{{ species }}_{{ spec['ENS_VERSION'] }}" ,
                    "-history_file": "$PROD_DIR/datachecks/history/st5.json",
                    "-secondary_release": "{{ NEXT_RELEASE_VERSION }}"
                },
                "arguments":[],
                "environ":{
                    "ENS_VERSION": "{{ spec['ENS_VERSION'] }}"
                }
            }
        }
    {% endblock %}
    {% block coreStats %}
        {
            "HOST": "CODON",
            "PipelineName": "CoreStats",
            "PipeConfig": "Bio::EnsEMBL::Production::Pipeline::PipeConfig::CoreStatistics_conf",
            "PipeParams": {
                "params": {
                     "-registry": "$REG_PROD_DIR/st5-w.pm ",
                     {{ pipe_param('species', species) }} ,
                     {{ pipe_param('division', division)  }} ,
                     "-pipeline_name": "core_stats_{{ species }}_{{ spec['ENS_VERSION'] }}" ,
                     "-history_file": "$PROD_DIR/datachecks/history/st5.json",
                     "-run_all": 0
                }, 
                "arguments":[],
                "environ":{
                    "ENS_VERSION": "{{ spec['ENS_VERSION'] }}"
                }
            }
        },
    {% endblock coreStats %}
    {% block proteinFeature %}
        {
            "HOST": "CODON",
            "PipelineName": "ProteinFeatures",
            "PipeConfig": "Bio::EnsEMBL::Production::Pipeline::PipeConfig::ProteinFeatures_conf",
            "PipeParams": {
                "params": {
                    "-registry": "$REG_PROD_DIR/st5-w.pm",
                    {{ pipe_param('species', species) }},
                    {{ pipe_param('division', division)  }},
                    "-pipeline_dir": "/hps/nobackup2/production/ensembl/ensprod/temp/protein_features",
                    "-config_file": "$PROD_DIR/datachecks/config/st5.json",
                    "-check_interpro_db_version": 1,
                    "-pipeline_name": "protein_feature_{{ species }}_{{ spec['ENS_VERSION'] }}",
                    "-uniparc_xrefs": 1,
                    "-uniprot_xrefs": 1
                },
                "arguments": [],
                "environ": {}
            }
        },
    {% endblock proteinFeature %}
    {% block RNAGeneXref %}
        {
            "HOST": "CODON",
            "PipelineName": "RNAGeneXref",
            "PipeConfig": "Bio::EnsEMBL::Production::Pipeline::PipeConfig::RNAGeneXref_conf",
            "PipeParams": {
                "params": {
                    "-registry": "$REG_PROD_DIR/st5-w.pm",
                    {{ pipe_param('species', species) }},
                    {{ pipe_param('division', division)  }},
                    "-pipeline_name": "RNA_xref_{{ species }}_{{ spec['ENS_VERSION'] }}",
                    "-config_file": "$PROD_DIR/datachecks/config/st5.json",
                    "-check_interpro_db_version": 1
                },
                "arguments": [],
                "environ": {}
            }
        },
    {% endblock RNAGeneXref %}
    {% block DumpSpeciesForGOA %}
        {
            "HOST": "CODON",
            "PipelineName": "DumpSpeciesForGOA",
            "PipeConfig": "Bio::EnsEMBL::Production::Pipeline::PipeConfig::DumpSpeciesForGOA_conf",
            "PipeParams": {
                "params": {
                    "-registry": "$REG_PROD_DIR/st5-w.pm",
                    {{ pipe_param('species', species) }},
                    {{ pipe_param('division', division)  }},
                    "-pipeline_name": "goa_{{ species }}_{{ spec['ENS_VERSION'] }}",
                    "-release": "{{ spec['ENS_VERSION'] }}"
                },
                "arguments": [],
                "environ": {}
            }
        },
    {% endblock DumpSpeciesForGOA %}

    {% block GPADAnnotation %} 
        
        {
            "HOST": "CODON",
            "PipelineName": "GPADAnnotation",
            "PipeConfig": "Bio::EnsEMBL::Production::Pipeline::PipeConfig::GPAD_conf",
            "PipeParams": {
                "params": {
                    "-registry": "$REG_PROD_DIR/st5-w.pm",
                    {{ pipe_param('species', species) }},
                    {{ pipe_param('division', division)  }},
                    "-pipeline_name": "gpad_{{ species }}_{{ spec['ENS_VERSION'] }}",
                    "-gpad_dirname": "ensemblrapid"
                },
                "arguments": [],
                "environ": {}
            }
        },
    {% endblock GPADAnnotation %}    
    {% block StableIDGeneration %}
        {
            "HOST": "CODON",
            "PipelineName": "UpdatePackedStatus",
            "PipeConfig": "Bio::EnsEMBL::Production::Pipeline::PipeConfig::StableIDs_conf",
            "PipeParams": {
                "params": {
                    "-registry": "$REG_PROD_DIR/st5-w.pm",
                    {{ pipe_param('species', species) }},
                    {{ pipe_param('division', division)  }},
                    "-pipeline_name": "stable_ids_{{ species }}_{{ spec['ENS_VERSION'] }}",
                    "-base_dir": "${BASE_DIR}",
                    "-srv_url": "$(st5-w details url)",
                    "-registry": "$REG_PROD_DIR/st5.pm",
                    "-db_name": "ensembl_stable_ids_${RR_ENS_VERSION}",
                    "-email": "ensembl-production@ebi.ac.uk",
                    "-incremental": 1
                },
                "arguments": [],
                "environ": {}
            }
        },
    {% endblock StableIDGeneration %}
    {% block GeneAutoComplete %}
        {
            "HOST": "CODON",
            "PipelineName": "GeneAutoComplete",
            "PipeConfig": "Bio::EnsEMBL::Production::Pipeline::PipeConfig::GeneAutoComplete_conf",
            "PipeParams": {
                "params": {
                    "-registry": "$REG_PROD_DIR/st5-w.pm",
                    {{ pipe_param('species', species) }},
                    {{ pipe_param('division', division)  }},
                    "-pipeline_name": "autocomplete_{{ species }}_{{ spec['ENS_VERSION'] }}",
                    "-base_dir": "${BASE_DIR}",
                    "-srv_url": "$(st5-w details url)",
                    "-registry": "$REG_PROD_DIR/st5.pm",
                    "-db_name": "ensembl_stable_ids_${RR_ENS_VERSION}",
                    "-email": "ensembl-production@ebi.ac.uk",
                    "-incremental": 1
                },
                "arguments": [],
                "environ": {}
            }
        },
    {% endblock GeneAutoComplete %} 
    {% block ProductionDBSync %}
        {
            "HOST": "CODON",
            "PipelineName": "ProductionDBSync",
            "PipeConfig": "Bio::EnsEMBL::Production::Pipeline::PipeConfig::ProductionDBSync_conf",
            "PipeParams": {
                "params": {
                    "-registry": "$REG_PROD_DIR/st5-w.pm",
                    {{ pipe_param('species', species) }},
                    {{ pipe_param('division', division)  }},
                    "-pipeline_name": "prod_sync_{{ species }}_{{ spec['ENS_VERSION'] }}",
                    "-group": "core,otherfeatures,rnaseq,variation",
                    "-history_file": "$PROD_DIR/datachecks/history/st5.json"
                },
                "arguments": [],
                "environ": {}
            }
        },
    {% endblock ProductionDBSync %}   
    {% block FTPDumps %}
        {
            "HOST": "CODON",
            "PipelineName": "FTPDumps",
            "PipeConfig": "Bio::EnsEMBL::Production::Pipeline::PipeConfig::FileDumpCore_conf",
            "PipeParams": {
                "params": {
                    "-dump_dir": "/nfs/production/panda/ensembl/production/ensemblftp/rapid-release", 
                    "-ftp_root": "/nfs/ensemblftp/PUBLIC/pub/rapid-release",
                    "-registry": "/nfs/panda/ensembl/production/registries/st5.pm",
                    "-pipeline_name": "dump_{{ species }}_{{ spec['ENS_VERSION'] }}",
                    "-rnaseq_email": "ensembl-genebuild@ebi.ac.uk",
                    "-production_queue": "production-rh74",
                    "-datamover_queue": "production-rh74",
                    {{ pipe_param('species', species) }},
                    {{ pipe_param('division', division)  }}
                },
                "arguments": [],
                "environ": {}
            }
        }
    {% endblock FTPDumps %}        
{% endblock flow %}
