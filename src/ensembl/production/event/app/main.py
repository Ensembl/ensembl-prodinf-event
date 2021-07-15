#!/usr/bin/env python

import re
import json
import logging
import os

from flask import Flask, request, jsonify, Response, redirect, url_for, render_template
from flask_cors import CORS
from flasgger import Swagger, SwaggerView, Schema, fields
from flask_bootstrap import Bootstrap


from ensembl.production.event.config import EventConfig as config
from ensembl.production.core import app_logging
from ensembl.production.core.models.hive import HiveInstance
from ensembl.production.core.exceptions import HTTPRequestError

from ensembl.production.core.amqp_publishing import AMQPPublisher
from ensembl.production.core.reporting import make_report, ReportFormatter

from ensembl.production.event.celery_app.tasks import initiate_pipeline
from ensembl.production.event.models.schema import HandoverSpec

from elasticsearch import Elasticsearch, TransportError, NotFoundError

# set static and template paths
app_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
static_path = os.path.join(app_path, 'static')
template_path = os.path.join(app_path, 'templates')
app = Flask(__name__, instance_relative_config=True, static_folder=static_path, template_folder=template_path,
            static_url_path='/static/events/')

#read event config
app.config.from_object('ensembl.production.event.config.EventConfig')

#set app logs
formatter = logging.Formatter(
    "[%(asctime)s] {%(pathname)s:%(lineno)d} %(levelname)s - %(message)s")
handler = app_logging.default_handler()
handler.setFormatter(formatter)
app.logger.addHandler(handler)

#set swagger config
app.config['SWAGGER'] = {
    'title': 'Ensembl Event Service',
    'uiversion': 3,
    'hide_top_bar': True,
    'ui_params': {
        'defaultModelsExpandDepth': -1
    },
    'favicon': '/img/production.png'
}
swagger = Swagger(app)
cors = CORS(app)
bootstrap = Bootstrap(app)
app.logger.info(app.config)
hives = {}
json_pattern = re.compile("application/json")
es_host = app.config['ES_HOST']
es_port = str(app.config['ES_PORT'])
es_index = app.config['ES_INDEX']

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
    
def get_hive(process):
    if process not in hives:
        if process not in process_lookup:
            raise ProcessNotFoundError('Process %s not known' % process)
        hives[process] = HiveInstance(process_lookup[process]['hive_uri'])
    return hives[process]


# Error Handling
class EventNotFoundError(Exception):
    """Exception showing event not found"""
    pass

@app.errorhandler(HTTPRequestError)
def handle_bad_request_error(e):
    app.logger.error(str(e))
    return jsonify(error=str(e)), e.status_code

@app.errorhandler(EventNotFoundError)
def handle_event_not_found_error(e):
    app.logger.error(str(e))
    return jsonify(error=str(e)), 404

@app.errorhandler(ProcessNotFoundError)
def handle_process_not_found_error(e):
    app.logger.error(str(e))
    return jsonify(error=str(e)), 404
  

class EventWorkflow(SwaggerView):
    parameters=HandoverSpec  
    tags = [ "Submit Event Workflow job " ]
    responses = {
        200: {
            "description": "Handover Token for Workflow",
        }
    }

    def post(self):
        """
        Submit Event Workflow Job
        """
        try:
            if json_pattern.match(request.headers['Content-Type']):
                job = request.json
                spec = job.get('spec', None)
                if spec and spec['handover_token']:
                    res = initiate_pipeline(spec)
                    if res['status']:
                        return redirect(url_for('qrp'))
                    raise ValueError(res['error'])
                else:
                    raise ValueError('spec and result object not fount in payload' )
            else:
                raise ValueError('application content should be in json ')
        except Exception as e:
            return Response(str(e) , status=400) 

class EventWorkflowJobStatus(SwaggerView):

    parameters = [
        {
            "name": "handover_token",
            "in": "path",
            "type": "string",
        },
        {
            "name": "format",
            "in": "path",
            "type": "string",
            "default": "json"
        }

    ]  
    tags = [ "Rapid Workflow job status" ]
    responses = {
        200: {
            "description": "Wokflow Job List",
        }
    }

    def get(self, handover_token=None):
        """
        Event Workflow Jobs List
        """
        try:
            format = request.args.get('format', None)

            if format and format == 'json':
                return render_template('ensembl/qrp/list.html')

            es = Elasticsearch([{'host': es_host, 'port': es_port}])
            if handover_token:
                res = es.search(index=es_index, body={
                        "query": {
                            "match": {

                                "handover_token": handover_token
                            }
                        },
                        "size": 1,
                        })
            else:
                res = es.search(index=es_index, body= {"size":300, "query": {"match_all": {}}})

            jobs = []

            for doc in res['hits']['hits']:
                jobs.append(doc['_source'])

            return jsonify(jobs)   
        except Exception  as e:
            return Response(str(e) , status=400)

class EventRecords(SwaggerView):
 
    tags = [ "Insert/Update Event Records in ElasticSearch" ]
    responses = {
        200: {
            "description": "Handover Token for Rapid Release Workflow",
        }
    }

    def post(self):
        """
        Submit Event Record into ElasticSearch
        """
        try:
            es = Elasticsearch([{'host': es_host, 'port': es_port}])
            if json_pattern.match(request.headers['Content-Type']):
                spec = request.json
                res = es.index(index=es_index, doc_type='jobs', id=spec['handover_token'], body=spec)
                return {'status': True, 'error': ''} 
        except Exception as e :
            return Response(str(e) , status=400)

        return {'status': True, 'error': ''}

    def put(self):
        """
        Update Event Record In ElasticSearch
        """
        try:
            es = Elasticsearch([{'host': es_host, 'port': es_port}])
            if json_pattern.match(request.headers['Content-Type']):
                spec = request.json
                res = es.update(index=es_index, doc_type='jobs', id=spec['handover_token'], body={ "doc": spec })
                return {'status': True, 'error': ''} 
        except Exception as e :
            return Response(str(e) , status=400)

app.add_url_rule(
    '/submit/workflow',
    view_func=EventWorkflow.as_view('SubmitWorkflow'),
    methods=['POST']
)

app.add_url_rule(
    '/workflows',
    view_func=EventWorkflowJobStatus.as_view('EventWorkflowJobStatus'),
    methods=['GET']
)

app.add_url_rule(
    '/workflows/<handover_token>',
    view_func=EventWorkflowJobStatus.as_view('EventWorkflowJobStatusHandover'),
    methods=['GET']
)

app.add_url_rule(
    '/add/record',
    view_func=EventRecords.as_view('InsertEventRecord'),
    methods=['POST']
)

app.add_url_rule(
    '/add/record',
    view_func=EventRecords.as_view('UpdateEventRecord'),
    methods=['PUT']
)

if __name__ == "__main__":
    app.run(debug=True)