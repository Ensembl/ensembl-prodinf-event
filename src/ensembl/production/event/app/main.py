#!/usr/bin/env python

import logging
from flask import Flask, request, jsonify
from flask_cors import CORS
import re
import json
from flasgger import Swagger, SwaggerView, Schema, fields

from ensembl.production.core.amqp_publishing import AMQPPublisher
from ensembl.production.core.reporting import make_report, ReportFormatter
from ensembl.production.core.models.hive import HiveInstance
from ensembl.production.core.exceptions import HTTPRequestError

from ensembl.production.event.celery.tasks import process_result
from ensembl.production.event.config import EventConfig as config


event_formatter = ReportFormatter('event_handler')
publisher = AMQPPublisher(config.report_server,
                          config.report_exchange,
                          exchange_type=config.report_exchange_type,
                          formatter=event_formatter)


app = Flask(__name__, instance_relative_config=True)
app.config.from_object('ensembl.production.event.config.EventConfig')
#app.logger.addHandler(app_logging.default_handler())
app.config['SWAGGER'] = {
    'title': 'Event App',
    'uiversion': 1
}
swagger = Swagger(app)




# app.logger.info(app.config)

def log_and_publish(report):
    """Handy function to mimick the logger/publisher behaviour.
    """
    level = report['report_type']
    routing_key = 'report.%s' % level.lower()
    app.logger.log(getattr(logging, level), report['msg'])
    publisher.publish(report, routing_key)


class EventNotFoundError(Exception):
    """Exception showing event not found"""
    pass


app.logger.info(config.event_lookup)
with open(config.event_lookup, 'r') as evt_file:
    event_lookup = json.load(evt_file)


def get_processes_for_event(event):
    event_type = event['type']
    if event_type not in event_lookup:
        raise EventNotFoundError('Event type %s not known' % event_type)
    return event_lookup[event_type]


class ProcessNotFoundError(Exception):
    """Exception showing process not found"""
    pass

with open(config.process_lookup, 'r') as proc_file:
    process_lookup = json.load(proc_file)


def get_analysis(process):
    if process not in process_lookup:
        raise ProcessNotFoundError('Process %s not known' % process)
    return process_lookup[process]['analysis']

hives = {}


def get_hive(process):
    if process not in hives:
        if process not in process_lookup:
            raise ProcessNotFoundError('Process %s not known' % process)
        hives[process] = HiveInstance(process_lookup[process]['hive_uri'])
    return hives[process]


cors = CORS(app)

# use re to support different charsets
json_pattern = re.compile("application/json")

@app.route('/', methods=['GET'])
def index():
    return {
        'title': 'Event App',
        'uiversion': 1
    }

# @app.route('/jobs', methods=['POST'])
# def submit_job():
#     """
#     Endpoint to submit an event to process
#     ---
#     tags:
#       - jobs
#     parameters:
#       - in: body
#         name: body
#         description: event
#         required: false
#         schema:
#           $ref: '#/definitions/submit'
#     operationId: jobs
#     consumes:
#       - application/json
#     produces:
#       - application/json
#     security:
#       submit_auth:
#         - 'write:submit'
#         - 'read:submit'
#     schemes: ['http', 'https']
#     deprecated: false
#     externalDocs:
#       description: Project repository
#       url: http://github.com/rochacbruno/flasgger
#     """
#     if json_pattern.match(request.headers['Content-Type']):
#         event = request.json
#         results = {"processes": [], "event": event}
#         # convert event to processes
#         processes = get_processes_for_event(event)
#         for process in processes:
#             log_and_publish(make_report('DEBUG', 'Submitting process %s' % process))
#             hive = get_hive(process)
#             analysis = get_analysis(process)
#             try:
#                 job = hive.create_job(analysis, {'event': event})
#             except ValueError as e:
#                 raise HTTPRequestError(str(e), 404)
#             event_task = process_result.delay(event, process, job.job_id)
#             results['processes'].append({
#                 "process":process,
#                 "job":job.job_id,
#                 "task":event_task.id
#             })
#         return jsonify(results);
#     else:
#         raise HTTPRequestError('Could not handle input of type %s' % request.headers['Content-Type'])


# @app.route('/jobs/<string:process>/<int:job_id>', methods=['GET'])
# def job(process, job_id):
#     """
#     Endpoint to retrieve a given job result for a process and job id
#     ---
#     tags:
#       - jobs
#     parameters:
#       - name: process
#         in: path
#         type: string
#         required: true
#         default: 1
#         description: process name
#       - name: job_id
#         in: path
#         type: integer
#         required: true
#         default: 1
#         description: id of the job
#     operationId: jobs
#     produces:
#       - application/json
#     security:
#       results_auth:
#         - 'write:results'
#         - 'read:results'
#     schemes: ['http', 'https']
#     deprecated: false
#     externalDocs:
#       description: Project repository
#       url: http://github.com/rochacbruno/flasgger
#     definitions:
#       job_id:
#         type: object
#         properties:
#           job_id:
#             type: integer
#             items:
#               $ref: '#/definitions/job_id'
#       result:
#         type: object
#         properties:
#           result:
#             type: string
#             items:
#               $ref: '#/definitions/result'
#     responses:
#       200:
#         description: Result of an event job
#         schema:
#           $ref: '#/definitions/job_id'
#     """
#     output_format = request.args.get('format')
#     if output_format == 'email':
#         email = request.args.get('email')
#         if email == None:
#             raise HTTPRequestError("Email not specified")
#         return results_email(request.args.get('email'), process, job_id)
#     elif output_format == None:
#         return results(process, job_id)
#     else:
#         raise HTTPRequestError('Format %s not known' % output_format)


# def results(process, job_id):
#     log_and_publish(make_report('INFO', 'Retrieving job from %s with ID %s' % (process, job_id)))
#     try:
#         job_result = get_hive(process).get_result_for_job_id(job_id)
#     except ValueError as e:
#         raise HTTPRequestError(str(e), 404)
#     return jsonify(job_result)


# @app.route('/jobs/<string:process>/<int:job_id>', methods=['DELETE'])
# def delete_job(process, job_id):
#     """
#     Endpoint to delete a given job result using job_id
#     ---
#     tags:
#       - jobs
#     parameters:
#       - name: process
#         in: path
#         type: string
#         required: true
#         default: 1
#         description: process name
#       - name: job_id
#         in: path
#         type: integer
#         required: true
#         default: 1
#         description: id of the job
#     operationId: jobs
#     consumes:
#       - application/json
#     produces:
#       - application/json
#     security:
#       delete_auth:
#         - 'write:delete'
#         - 'read:delete'
#     schemes: ['http', 'https']
#     deprecated: false
#     externalDocs:
#       description: Project repository
#       url: http://github.com/rochacbruno/flasgger
#     definitions:
#       job_id:
#         type: object
#         properties:
#           job_id:
#             type: integer
#             items:
#               $ref: '#/definitions/job_id'
#       id:
#         type: integer
#         properties:
#           id:
#             type: integer
#             items:
#               $ref: '#/definitions/id'
#     responses:
#       200:
#         description: Job_id that has been deleted
#         schema:
#           $ref: '#/definitions/job_id'
#         examples:
#           id: 1
#     """
#     hive = get_hive(process)
#     job = hive.get_job_by_id(job_id)
#     try:
#         hive.delete_job(job)
#     except ValueError as e:
#         raise HTTPRequestError(str(e), 404)
#     return jsonify({"id":job_id, "process": process})


# def results_email(email, process, job_id):
#     log_and_publish(make_report('INFO', 'Retrieving job with ID %s for %s' % (job_id, email)))
#     hive = get_hive(process)
#     try:
#         job = hive.get_job_by_id(job_id)
#         results = hive.get_result_for_job_id(job_id)
#     except ValueError as e:
#         raise HTTPRequestError(str(e), 404)
#     # TODO
#     results['email'] = email
#     return jsonify(results)


# @app.route('/jobs/<string:process>', methods=['GET'])
# def jobs(process):
#     """
#     Endpoint to retrieve all the jobs results from the database
#     ---
#     tags:
#       - jobs
#     parameters:
#       - name: process
#         in: path
#         type: string
#         required: true
#         default: 1
#         description: process name
#     operationId: jobs
#     consumes:
#       - application/json
#     produces:
#       - application/json
#     security:
#       jobs_auth:
#         - 'write:jobs'
#         - 'read:jobs'
#     schemes: ['http', 'https']
#     deprecated: false
#     externalDocs:
#       description: Project repository
#       url: http://github.com/rochacbruno/flasgger
#     responses:
#       200:
#         description: Retrieve all the jobs results from the database
#         schema:
#           $ref: '#/definitions/job_id'
#     """
#     log_and_publish(make_report('INFO', 'Retrieving jobs'))
#     return jsonify(get_hive(process).get_all_results(get_analysis(process)))


# @app.route('/events')
# def events():
#     """
#     Endpoint to retrieve all known event types
#     ---
#     tags:
#       - events
#     operationId: events
#     produces:
#       - application/json
#     security:
#       jobs_auth:
#         - 'write:jobs'
#         - 'read:jobs'
#     schemes: ['http', 'https']
#     deprecated: false
#     externalDocs:
#       description: Project repository
#       url: http://github.com/rochacbruno/flasgger
#     responses:
#       200:
#         description: Retrieve all the events
#     """
#     return jsonify(list(event_lookup.keys()))


# @app.route('/processes')
# def processes():
#     """
#     Endpoint to retrieve all known processes handled
#     ---
#     tags:
#       - processes
#     operationId: processes
#     produces:
#       - application/json
#     security:
#       jobs_auth:
#         - 'write:jobs'
#         - 'read:jobs'
#     schemes: ['http', 'https']
#     deprecated: false
#     externalDocs:
#       description: Project repository
#       url: http://github.com/rochacbruno/flasgger
#     responses:
#       200:
#         description: Retrieve all the processes
#     """
#     return jsonify(list(process_lookup.keys()))


# #####QRP#######
# @app.route('/qrp/submit/job', methods=['POST'])
# def qrp_submit():
#     """ Submit and start producton pipelines based on the division, dbtype """
#     try:
#         if json_pattern.match(request.headers['Content-Type']):
#             job = request.json
#             spec = job.get('spec', None)
#             print('HIII')
#             print(spec)
#             if spec and spec['handover_token']:#and events :
#                   print('init start')
#                   res = initiate_pipeline(spec)
#                   print('init end')
#                   if res['status']:
#                       print(url_for('qrp'))
#                       return redirect(url_for('qrp'))
#                   raise Exception(res['error'])
#             else:
#                 raise Exception('spec and result object not fount in payload' )
#         else:
#             raise Exception('application content should be in json ')
        
#     except Exception as e:
#         print("eeeeeeeeeeeeeee") 
#         print(e)
#         return Response(str(e) , status=400) 




# @app.route('/qrp/jobs', methods=['GET'])
# @app.route('/qrp/jobs/<string:handover_token>', methods=['GET'])
# def qrp(handover_token=None):
#     """
#     Get the status for all qrp jobs 
#     """
#     try:
#         format = request.args.get('format', None)
#         es = Elasticsearch([{'host': es_host, 'port': es_port}])
#         if handover_token:
#             res = es.search(index="pipelines", body={
#                     "query": {
#                         "match": {

#                             "handover_token": handover_token
#                         }
#                      },
#                      "size": 1,
#                     })
#         else:
#             res = es.search(index="pipelines", body= {"size":300, "query": {"match_all": {}}})
#         jobs = []
#         for doc in res['hits']['hits']:
#             jobs.append(doc['_source'])
#     except Exception  as e:
#         return Response(str(e) , status=400)
    
#     if format and format == 'json':
#         return jsonify(jobs)
    
#     return jsonify(jobs) #ender_template('ensembl/qrp/list.html') #{'jobs': jobs}

# @app.route('/qrp/jobs', methods=['POST', 'PUT'])
# def qrp_insert():
#     """
#     Insert/Update record into ES
#     """
#     try:
#         es = Elasticsearch([{'host': es_host, 'port': es_port}])
#         if json_pattern.match(request.headers['Content-Type']):
#             #logger.debug("insert record " + str(request.json))
#             spec = request.json
#             if request.method == 'POST':
#                 res = es.index(index='pipelines',doc_type='jobs', id=spec['handover_token'], body=spec)
#             if request.method == 'PUT':
#                 res = es.update(index='pipelines',doc_type='jobs', id=spec['handover_token'], body={ "doc": spec })
#             return {'status': True}
#     except Exception as e :
#         return Response(str(e) , status=400)

#     return {'status': True, 'error': ''}


# # @app.errorhandler(HTTPRequestError)
# # def handle_bad_request_error(e):
# #     app.logger.error(str(e))
# #     return jsonify(error=str(e)), e.status_code


# # @app.errorhandler(EventNotFoundError)
# # def handle_event_not_found_error(e):
# #     app.logger.error(str(e))
# #     return jsonify(error=str(e)), 404


# # @app.errorhandler(ProcessNotFoundError)
# # def handle_process_not_found_error(e):
# #     app.logger.error(str(e))
# #     return jsonify(error=str(e)), 404

