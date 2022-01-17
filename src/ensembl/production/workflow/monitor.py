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

import sys
import radical.saga as saga
import json
import re
import time

from sqlalchemy import create_engine, Column, Integer, String, ForeignKey, VARCHAR, func
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
__all__ = ['RemoteCmd']

Base = declarative_base()


class Beekeeper(Base):
    __tablename__ = 'beekeeper'

    beekeeper_id = Column(Integer, primary_key=True)
    cause_of_death = Column(String)
    loop_until = Column(String)

    def __repr__(self):
        return "<beekeeper(beekeeper_id='%s', cause_of_death='%s')>" % (
            self.beekeeper_id, self.cause_of_death)

class Worker(Base):
    __tablename__ = 'worker'

    worker_id  = Column(Integer, primary_key=True)
    process_id = Column(Integer)
    cause_of_death = Column(VARCHAR)
    status = Column(VARCHAR)

    def __repr__(self):
        return "<Worker(worker_id='%s', process_id='%s')>" % (
            self.worker_id, self.process_id)

class Role(Base):
    __tablename__ = 'role'

    role_id    = Column(Integer, primary_key=True)
    worker_id  = Column(Integer)
    
    def __repr__(self):
        return "<Role(role_id='%s', worker_id='%s')>" % (
            self.role_id, self.worker_id)


class Job(Base):
    __tablename__ = 'job'

    job_id  = Column(Integer, primary_key=True)
    role_id  = Column(Integer)
    status   = Column(VARCHAR)
    
    def __repr__(self):
        return "<JOB(job_id='%s', status='%s')>" % (
            self.job_id, self.status)

 

class RemoteCmd():

    def __init__(self, **kwargs):
        self.REMOTE_HOST = kwargs.get('REMOTE_HOST', None)
        self.ADDRESS = kwargs.get('ADDRESS', None)  # Address of your server
        self.USER = kwargs.get('USER', 'vinay')  # Username
        self.PASSWORD = kwargs.get('PASSWORD', '')  # That's amazing I got the same combination on my luggage!
        self.WORKING_DIR = kwargs.get('WORKING_DIR', None)  # Your working directory
        self.mysql_url = kwargs.get('mysql_url', None)  # hive database string
        self.ctx = saga.Context("ssh")
        self.ctx.user_id = self.USER
        if self.PASSWORD:
            self.ctx.user_pass = self.PASSWORD
        self.session = saga.Session()
        self.session.add_context(self.ctx)


    def run_job(self, **kwargs):
        """
        Execute Remote command through ssh
        return: {'status': boolean, 'error': str, 'state': str }
        """
        try:
            jd = saga.job.Description()
            jd.executable = kwargs['command']
            jd.arguments = kwargs['args']
            jd.output = kwargs.get("stdout", 'stdout.log')
            jd.error = kwargs.get("stderr", 'stderr.log')
            jd.working_directory = kwargs.get('pwd', self.WORKING_DIR)
            js = saga.job.Service('ssh://' + self.ADDRESS, session=self.session)
            job_synchronus = kwargs.get('synchronus', False)
            myjob = js.create_job(jd)
            myjob.run()
            if job_synchronus:
                myjob.wait()
                if myjob.exit_code != 0:
                    return {'status': False, 'state': myjob.state,
                            'error': 'Failed to run the job check stderr:' + jd.working_directory}

            return {'status': True, 'error': '', 'state': myjob.state, 'job_id': myjob.id }
        except Exception as e:
            print(str(e))
            return {'status': False, 'error': str(e)}


    def job_status(self, job_id, stop_job=False):
        """
        Get the job status / Stop the submitted job 
        """
        try:        

            service = saga.job.Service('ssh://' + self.ADDRESS, session=self.session)
            #stop the running jobs
            job = service.get_job(job_id)
            if stop_job:
                if job.get_state() in  [ saga.job.PENDING, saga.job.RUNNING ]:
                    job.cancel()
                else:
                    raise ValueError('Job already stopped')

            return {'status': True, 'error': '', 'job_status': job.get_state() }

        except Exception as e:
            return {'status': False, 'error': str(e)}

    def beekeper_status(self, mysql_url=None):
        """
        Check beekeeper executed all the jobs
        """
        try:

            engine = create_engine(mysql_url, pool_recycle=3600, echo=False)
            hive_session = sessionmaker()
            hive_session.configure(bind=engine)  
            s = hive_session()  
            result = s.query(Beekeeper).order_by(Beekeeper.beekeeper_id.desc()).first()
            if (result == None):
                raise ValueError('No Records')
            
            return {'status': True, 'error': '', 'value': result.cause_of_death}

        except  Exception as e:
            return {'status': False, 'error': str(e), 'value': ''}



    def stop_hive_jobs(self, mysql_url=None):
        """
        Kill all running hive jobs in farm with LSF IDs
        """
        try:

            engine = create_engine(mysql_url, pool_recycle=3600, echo=False)
            hive_session = sessionmaker()
            hive_session.configure(bind=engine)  
            s = hive_session()  
            result = s.query(Worker).join(Role, Worker.worker_id == Role.worker_id).join(Job, Job.role_id == Role.role_id).filter(Job.status == 'RUN').all()
            if (result == None):
                return {'status': False, 'error': 'No Running Jobs To Stop' }
                
            job_ids = ""
            command = 'bsub -I -q production -M 2000 -R "rusage[mem=2000]" bkill -J '
            for row in result:
                job_ids = job_ids + str(row.process_id) + ' '

            
            job_kill_status = self.run_job(command=command, args=job_ids, synchronus=True)
            
            return job_kill_status
            
        except  Exception as e:
            return {'status': False, 'error': str(e)}    

        