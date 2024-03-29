#!/usr/bin/env python
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
import json
import jinja2
import re
import subprocess
from typing import Optional


def sysCmd(command):  
    out = subprocess.run(command.split(' '),
                         text=True)
    if out.returncode != 0:
        raise RuntimeError("System command returned an error %s" % out.stderr)
    else:
        return out.stdout


class WorkflowDispatcher:
    """[Constructs Workflow template for given dbtype/division/species]

    Args:
        dbtype (str): [Database Type to select the workflow template]
        division (str, optional): [Division name to select workflow template]. Defaults to None.
        species (str, optional): [Species name to select workflow template]. Defaults to None.
    """   
    
    template_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'tpl')
    templateLoader = jinja2.FileSystemLoader(template_dir)
    templateEnv = jinja2.Environment(loader=templateLoader)
    templateEnv.globals['sysCommand'] = sysCmd

    def __init__(self, dbtype:str, division:Optional[str]=None, species:Optional[str]=None):                
        self.dbtype = dbtype
        self.division = division
        self.species = species

    def _get_template(self) -> str:
        """[Try to find from most specific to generic template to get automated process description]

        Returns:
            [str]: [template path]
        """        
        template_file = '{tpl_dir}/{tpl_file}.json.tpl'.format(tpl_dir=self.dbtype, tpl_file=self.species)
        if os.path.isfile(os.path.join(self.template_dir, template_file)):
            return template_file
        else:
            template_file = '{tpl_dir}/{tpl_file}.json.tpl'.format(tpl_dir=self.dbtype, tpl_file=self.division)
            if os.path.isfile(os.path.join(self.template_dir, template_file)):
                return template_file
            else:
                template_file = '{tpl_dir}/{tpl_file}.json.tpl'.format(tpl_dir=self.dbtype, tpl_file=self.dbtype)
                if os.path.isfile(os.path.join(self.template_dir, template_file)):
                    return template_file
        # default fail over to dbtype/dbtype.json.tpl
        return 'base.json.tpl'

    def create_template(self, spec: dict, division: Optional[str]=None, species: Optional[str]=None, antispecies: Optional[str]=None) -> dict:                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                            
        """[Creates Workflow template from given tpl files]

        Args:
            spec (dict): [Handover payload details]
            division (str, optional): [Division information for pipeline ]. Defaults to None.
            species (str, optional): [Species information for pipeline]. Defaults to None.
            antispecies (str, optional): [Species name not to inclue in pipeline]. Defaults to None.

        Returns:
            dict: [Workflow template with pipeline arguments]
        """         
        template = WorkflowDispatcher.templateEnv.get_template(self._get_template())
        flow_json = template.render(spec=spec, division=division, species=species, antispecies=antispecies)
        return json.loads(flow_json)  # this is where to put args to the template renderer

# obj = WorkflowDispatcher('test', division='plants', species='triticum_aestivum_jagger')
# flow = obj.create_template({
# 			"src_uri": "mysql://ensro@mysql-ens-plants-prod-1:4243/malus_domestica_golden_variation_52_105_1",
# 			"database": "malus_domestica_golden_variation_52_105_1",
# 			"contact": "gnaamati@ebi.ac.uk",
# 			"comment": "variation handover after SIFT run",
# 			"handover_token": "48d9a56c-dffe-11eb-909f-005056ab00f0",
# 		}, division='plants', species='triticum_aestivum_jagger')
# print(flow)
