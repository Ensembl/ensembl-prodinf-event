{% extends "base.json.tpl" %}

{% block flow %}
    {% block coreStats %}
        {
            "PipelineName": "CoreStats",
            "PipeConfig": "Bio::EnsEMBL::Production::Pipeline::PipeConfig::CoreStatistics_conf",
            "PipeParams": {
                "params": {
		         "-registry": "$REG_PROD_DIR/st5-w.pm ",	
                 {{ pipe_param('species', species) }} ,
                 {{ pipe_param('division', division)  }} ,
                 "-antispecies": "sars_cov_2" ,
                 "-pipeline_name": "rr_core_stats_{{ species }}_{{ spec['ENS_VERSION'] }}" ,
                 "-history_file": "$PROD_DIR/datachecks/history/st5.json"
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
                    "-pipeline_name": "rr_protein_features_{{ species }}_{{ spec['ENS_VERSION'] }}",
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
            "PipelineName": "RNAGeneXref",
            "PipeConfig": "Bio::EnsEMBL::Production::Pipeline::PipeConfig::RNAGeneXref_conf",
            "PipeParams": {
                "params": {
                    "-registry": "$REG_PROD_DIR/st5-w.pm",
                    {{ pipe_param('species', species) }},
                    {{ pipe_param('division', division)  }},
                    "-pipeline_name": "rr_RNA_gene_xref_{{ species }}_{{ spec['ENS_VERSION'] }}",
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
            "PipelineName": "DumpSpeciesForGOA",
            "PipeConfig": "Bio::EnsEMBL::Production::Pipeline::PipeConfig::DumpSpeciesForGOA_conf",
            "PipeParams": {
                "params": {
                    "-registry": "$REG_PROD_DIR/st5-w.pm",
                    {{ pipe_param('species', species) }},
                    {{ pipe_param('division', division)  }},
                    "-pipeline_name": "rr_dump_specie_for_GOA_{{ species }}_{{ spec['ENS_VERSION'] }}",
                    "-antispecies": "sars_cov_2" ,
                    "-release": "{{ spec['ENS_VERSION'] }}"
                },
                "arguments": [],
                "environ": {}
            }
        },
    {% endblock DumpSpeciesForGOA %}

    {% block GPADAnnotation %} 
        
        {
            "PipelineName": "GPADAnnotation",
            "PipeConfig": "Bio::EnsEMBL::Production::Pipeline::PipeConfig::GPAD_conf",
            "PipeParams": {
                "params": {
                    "-registry": "$REG_PROD_DIR/st5-w.pm",
                    {{ pipe_param('species', species) }},
                    {{ pipe_param('division', division)  }},
                    "-pipeline_name": "rr_gpad_load_{{ species }}_{{ spec['ENS_VERSION'] }}",
                    "-gpad_dirname": "ensemblrapid"
                },
                "arguments": [],
                "environ": {}
            }
        },
    {% endblock GPADAnnotation %}    
    {% block StableIDGeneration %}
        {
            "PipelineName": "UpdatePackedStatus",
            "PipeConfig": "Bio::EnsEMBL::Production::Pipeline::PipeConfig::StableIDs_conf",
            "PipeParams": {
                "params": {
                    "-registry": "$REG_PROD_DIR/st5-w.pm",
                    {{ pipe_param('species', species) }},
                    {{ pipe_param('division', division)  }},
                    "-pipeline_name": "rr_ensembl_stable_ids_{{ species }}_{{ spec['ENS_VERSION'] }}",
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
            "PipelineName": "GeneAutoComplete",
            "PipeConfig": "Bio::EnsEMBL::Production::Pipeline::PipeConfig::GeneAutoComplete_conf",
            "PipeParams": {
                "params": {
                    "-registry": "$REG_PROD_DIR/st5-w.pm",
                    {{ pipe_param('species', species) }},
                    {{ pipe_param('division', division)  }},
                    "-pipeline_name": "rr_ensembl_stable_ids_{{ species }}_{{ spec['ENS_VERSION'] }}",
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
            "PipelineName": "GeneAutoComplete",
            "PipeConfig": "Bio::EnsEMBL::Production::Pipeline::PipeConfig::ProductionDBSync_conf",
            "PipeParams": {
                "params": {
                    "-registry": "$REG_PROD_DIR/st5-w.pm",
                    {{ pipe_param('species', species) }},
                    {{ pipe_param('division', division)  }},
                    "-pipeline_name": "rr_production_dbsync_{{ species }}_{{ spec['ENS_VERSION'] }}",
                    "-group": "core,otherfeatures,rnaseq,variation",
                    "-history_file": "$PROD_DIR/datachecks/history/st5.json",
                    "-antispecies": "sars_cov_2"
                },
                "arguments": [],
                "environ": {}
            }
        },
    {% endblock ProductionDBSync %}   
    {% block FTPDumps %}
        {
            "PipelineName": "FTPDumps",
            "PipeConfig": "Bio::EnsEMBL::Production::Pipeline::PipeConfig::FileDumpCore_conf",
            "PipeParams": {
                "params": {
                    "-dump_dir": "/nfs/production/panda/ensembl/production/ensemblftp/rapid-release", 
                    "-ftp_root": "/nfs/ensemblftp/PUBLIC/pub/rapid-release",
                    "-registry": "/nfs/panda/ensembl/production/registries/st5.pm",
                    "-pipeline_name": "rr_file_dump_core_{{ species }}_{{ spec['ENS_VERSION'] }}",
                    "-antispecies": "sars_cov_2",
                    "-rnaseq_email": "ensembl-genebuild@ebi.ac.uk",
                    "-production_queue": "production-rh74",
                    "datamover_queue": "production-rh74",
                    {{ pipe_param('species', species) }},
                    {{ pipe_param('division', division)  }}
                },
                "arguments": [],
                "environ": {

                }
            }
        }
    {% endblock FTPDumps %}        
{% endblock flow %}
