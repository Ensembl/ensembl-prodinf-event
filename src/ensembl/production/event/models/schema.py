from flasgger import Swagger, SwaggerView, Schema, fields
from marshmallow.validate import OneOf

class HandoverSpec(Schema):
    
    handover_token = fields.UUID(metadata={'description': 'Handover Token UID',
                                       'example': '3729-jhshs-12929-1mssn'}, required=True)
    src_uri = fields.Str(metadata={'description': 'Mysql Source URI',
                                       'example': 'mysql://user:pass@host:3366/dbname'}, required=True)   
    database = fields.Str(metadata={'description': 'Database to handover',
                                       'example': 'malus_domestica_golden_variation_52_105_1'}, required=True)
    contact = fields.Str(metadata={'description': 'user email id',
                                       'example': 'user@ebi.ac.uk'}, required=True) 
    comment = fields.Str(metadata={'description': 'user comment',
                                       'example': 'Handover homosapiens for release 105'}, required=True)   
    source  = fields.Str(metadata={'description': 'source ',
                                       'example': 'Handover source'  }, default='Handover')   
    tgt_uri = fields.Str(metadata={'description': 'Target source db  ',
                                       'example': 'mysql://user:pass@mysql-ens-sta-3-b:port/malus_domestica_golden_variation_52_105_1' })  
    staging_uri = fields.Str(metadata={'description': 'stating URI  ',
                                       'example': 'mysql://user:pass@mysql-ens-sta-3-b:port/'})   
    db_division = fields.Str(metadata={'description': 'Division of handover database',
                                       'example': 'plants'}, required=True)
    db_type = fields.Str(metadata={'description': 'Database type ',
                                       'example': 'core'}, required=True)   
    ENS_VERSION = fields.Int(metadata={'description': 'Ensembl release number' , 'example': '105'}, required=True)  
    EG_VERSION = fields.Int(metadata={'description': 'Ensembl Genomes release number', 'example': '52'}, required=True) 
    RR_VERSION = fields.Int(metadata={'description': 'Rapid Release number', 'example': '24'}, required=True)    

class RestartHandoverSpec(Schema):
    handover_token = fields.UUID(metadata={'description': 'Handover Token UID',
                                       'example': '3729-jhshs-12929-1mssn'}, required=True)

    restart_type =  fields.Str(required=True, validate=OneOf(['BEEKEEPER',
                                          'INIT_PIPELINE',
                                          'SKIP_CURRENT_PIPELINE',
                                          'WORKFLOW']),
                                           metadata={'description': 'Restart BEEKEEPER/PIPELINE/WORKFLOW',
                                           'example': 'BEEKEEPER'}, default="BEEKEEPER")

class StopHandoverSpec(Schema):
    handover_token = fields.UUID(metadata={'description': 'Handover Token UID',
                                       'example': '3729-jhshs-12929-1mssn'}, required=True)

    job_id = fields.Str(metadata={'description': 'pipeline job_id for running pipeline'}, required=False)

    pipeline_name = fields.Str(metadata={'description': 'Pipeline name to stop celery job'}, required=False) 


    
