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

def construct_pipeline(job: dict, spec: dict) -> dict:
    """[Construct command line arguments for radical saga to run pipeline]

    Args:
        job (dict): [Handover payload details]
        spec (dict): [Current job details]

    Returns:
        dict: [Pipeline commandline details for radical saga to run pipeline]
    """

    hive_dbname = f"{spec['user']}_{job['PipeParams']['params']['-pipeline_name']}"
    queue_name = 'production-rh74' if job.get('HOST', None) == 'NOAH' else 'production'
    bsub_cmd = '' if  job.get('TEST', None) == "TRUE" else 'bsub -I -q ' + queue_name + ' -M 2000 -R "rusage[mem=2000]"'
    db_uri = spec['hive_url'] + hive_dbname

    temp = {
        'init': {'command': [], 'args': [], 'stdout': '', 'stderr': ''},
        'beekeeper': {'command': [f"{bsub_cmd} beekeeper.pl"], 'args': [], 'stdout': '', 'stderr': ''}
    }

    # for init pipeline
    for key, value in job['PipeParams']['params'].items():

        if key in ('-division', '-species', '-antispecies', '-group'):
            for each_item in value.split(','):
                temp['init']['args'].append(key)
                temp['init']['args'].append(each_item)
        else:
            temp['init']['args'].append(key)
            temp['init']['args'].append(value)

    for value in job['PipeParams']['arguments']:
        temp['init']['args'].append(value)

    for key, value in job['PipeParams']['environ'].items():
        temp['init']['command'].append(key + '=' + str(value))
        temp['init']['command'].append(' && ')

    temp['init']['args'].append('-pipeline_url ')
    temp['init']['args'].append(db_uri)
    temp['init']['args'].append('-hive_force_init')
    temp['init']['args'].append(1)

    temp['init']['command'].append(f"{bsub_cmd} init_pipeline.pl")
    temp['init']['command'].append(job['PipeConfig'])
    temp['init']['command'].append(' ')
    temp['init']['stdout'] = hive_dbname + ".stdout"
    temp['init']['stderr'] = hive_dbname + ".stderr"

    # for beekeeper
    temp['beekeeper']['args'].append('-url')
    temp['beekeeper']['args'].append(db_uri)
    # check if init pipelie has registry as option
    if '-registry' in job['PipeParams']['params']:
        temp['beekeeper']['args'].append('-reg_conf')
        temp['beekeeper']['args'].append(job['PipeParams']['params']['-registry'])

    temp['beekeeper']['args'].append('-loop')
    temp['beekeeper']['stdout'] = hive_dbname + ".beekeeper.stdout"
    temp['beekeeper']['stderr'] = hive_dbname + ".beekeeper.stderr"
    temp['mysql_url'] = db_uri
    temp['HOST'] = job.get('HOST', None)
    return temp
