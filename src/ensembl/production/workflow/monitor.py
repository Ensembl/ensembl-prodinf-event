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
    process_id = Column(VARCHAR)
    cause_of_death = Column(VARCHAR)

    def __repr__(self):
        return "<beekeeper(worker_id='%s', process_id='%s')>" % (
            self.worker_id, self.process_id)

class RemoteCmd():

    def __init__(self, **args):
        self.REMOTE_HOST = args.get('REMOTE_HOST', None)
        self.ADDRESS = args.get('ADDRESS', None)  # Address of your server
        self.USER = args.get('USER', 'vinay')  # Username
        self.PASSWORD = args.get('PASSWORD', '')  # That's amazing I got the same combination on my luggage!
        self.WORKING_DIR = args.get('WORKING_DIR', None)  # Your working directory
        self.mysql_url = args.get('mysql_url', None)  # hive database string
        self.ctx = saga.Context("ssh")
        self.ctx.user_id = self.USER
        self.session = saga.Session()
        self.session.add_context(self.ctx)


    def run_job(self, **args):
        """
        Execute Remote command through ssh
        return: {'status': boolean, 'error': str, 'state': str }
        """
        try:
            jd = saga.job.Description()
            jd.executable = args['command']
            jd.arguments = args['args']
            jd.output = args.get("stdout", 'stdout.log')
            jd.error = args.get("stderr", 'stderr.log')
            jd.working_directory = args.get('pwd', self.WORKING_DIR)
            js = saga.job.Service('ssh://' + self.ADDRESS, session=self.session)
            job_synchronus = args.get('synchronus', False)
            myjob = js.create_job(jd)
            print("\n...starting job...\n")
            # Now we can start our job.
            myjob.run()
            print("Job ID    : %s" % (myjob.id))
            print("Job State : %s" % (myjob.state))
            if job_synchronus:
                print("\n...waiting for job to complete...\n")
                # wait for the job to either finish or fail
                myjob.wait()
                print("Job State : %s" % (myjob.state))
                print("Exitcode  : %s" % (myjob.exit_code))
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

            
    
  
