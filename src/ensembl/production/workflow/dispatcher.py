import os
import json
import jinja2
import re
import subprocess

def sysCmd(command):
    out = subprocess.run(command.split(' '),
                         text=True)
    if out.returncode != 0:
        raise RuntimeError("System command returned an error %s" % out.stderr)
    else:
        return out.stdout


class WorkflowDispatcher():

    template_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'tpl')
    templateLoader = jinja2.FileSystemLoader(template_dir)
    templateEnv = jinja2.Environment(loader=templateLoader)
    templateEnv.globals['sysCommand'] = sysCmd

    def __init__(self, dbtype, division=None, species=None):
        self.dbtype = dbtype
        self.division = division
        self.species = species

    def _get_template(self):
        """
        Try to find from most specific to generic template to get automated process description
        :return: str the template path
        """
        template_file = '{tpl_dir}/{tpl_file}.json.tpl'.format(tpl_dir=self.dbtype, tpl_file=self.species)
        print(template_file)
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
        print( os.path.isfile(os.path.join(self.template_dir, template_file)))
        print(os.path.join(self.template_dir, template_file))
        return 'base.json.tpl'

    def create_template(self, spec, division=None, species=None, antispecies=None):
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
