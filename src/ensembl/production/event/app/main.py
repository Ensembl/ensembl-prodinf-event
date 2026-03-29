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

import re
import json
import logging
import os

from flask import Flask, request, jsonify, Response, redirect, url_for, render_template
from flask_cors import CORS
from flasgger import Swagger, SwaggerView, Schema, fields
from flask_bootstrap import Bootstrap
from celery import states

from ensembl.production.event.config import EventConfig as config
from ensembl.production.core import app_logging
from ensembl.production.core.models.hive import HiveInstance
from ensembl.production.core.exceptions import HTTPRequestError

from ensembl.production.core.amqp_publishing import AMQPPublisher
from ensembl.production.core.reporting import make_report, ReportFormatter

from ensembl.production.event.celery_app.tasks import initiate_pipeline, restart_workflow, stop_running_job
from ensembl.production.core.es import ElasticsearchConnectionManager
from ensembl.production.event.models.schema import HandoverSpec, RestartHandoverSpec, StopHandoverSpec

from elasticsearch import Elasticsearch, TransportError, NotFoundError

# set static and template paths
app_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
static_path = os.path.join(app_path, 'static')
template_path = os.path.join(app_path, 'templates')
app = Flask(__name__, instance_relative_config=True, static_folder=static_path, template_folder=template_path,
            static_url_path='/static/events/')

# read event config
app.config.from_object('ensembl.production.event.config.EventConfig')

# set app logs
formatter = logging.Formatter(
    "[%(asctime)s] {%(pathname)s:%(lineno)d} %(levelname)s - %(message)s")
handler = app_logging.default_handler()
handler.setFormatter(formatter)
app.logger.addHandler(handler)

# set swagger config
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
es_user = app.config['ES_USER']
es_password = app.config['ES_PASSWORD']
es_ssl = app.config['ES_SSL']
app.url_map.strict_slashes = False

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
    parameters = HandoverSpec
    tags = ["Submit Event Workflow job "]
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

                errors = HandoverSpec().validate(request.json)
                if errors:
                    raise ValueError(errors)

                job = request.json
                # spec = job.get('spec', None)
                if job and job['handover_token']:

                    # check workflow with handover_token exists
                    res = EventWorkflowJobStatus().get(handover_token=job['handover_token'])
                    spec = res.get_json()

                    if spec is not None and len(spec) > 0:
                        raise ValueError(
                            f"Workflow with handover token {job['handover_token']} already exist, restart the workflow if needed")

                    # start the workflow
                    res = initiate_pipeline(job)
                    if res['status']:
                        return res
                        # return redirect(url_for('EventWorkflowJobStatus'))
                    else:
                        raise ValueError(res['error'])
                else:
                    raise ValueError('spec and result object not fount in payload')
            else:
                raise ValueError('application content should be in json ')
        except Exception as e:
            return Response(str(e), status=400)


class EventRestartWorkflow(SwaggerView):
    parameters = RestartHandoverSpec
    tags = ["Restart Event Workflow "]
    responses = {
        200: {
            "description": "Handover Token for Workflow",
        }
    }

    def post(self):
        """
        Restart Event Workflow 
        """
        try:

            if json_pattern.match(request.headers['Content-Type']):
                errors = RestartHandoverSpec().validate(request.json)
                job = request.json

                if errors:
                    raise ValueError(errors)

                res = EventWorkflowJobStatus().get(handover_token=job['handover_token'])
                spec = res.get_json()

                if spec is None or len(spec) == 0:
                    raise ValueError(f"handover token {job['handover_token']} not found")

                spec = spec[0]

                if spec['params']['status']:
                    raise ValueError(f"Workflow for handover token {job['handover_token']} is still running, Stop it")

                status = restart_workflow(job['restart_type'], spec['params'])

                return redirect(url_for('EventWorkflowJobStatusHandover', handover_token=job['handover_token']))


        except Exception as e:
            return Response(str(e), status=400)


class EventStopWorkflow(SwaggerView):
    parameters = StopHandoverSpec
    tags = ["Stop Event Workflow "]
    responses = {
        200: {
            "description": "Handover Token for Workflow",
        }
    }

    def post(self):
        """
        Stop Event Workflow 
        """
        try:

            if json_pattern.match(request.headers['Content-Type']):
                errors = StopHandoverSpec().validate(request.json)
                job = request.json

                if errors:
                    raise ValueError(errors)

                res = EventWorkflowJobStatus().get(handover_token=job['handover_token'])
                spec = res.get_json()

                if spec is None or len(spec) == 0:
                    raise ValueError(f"handover token {job['handover_token']} not found")

                spec = spec[0]
                if spec['params']['workflow'] == 'Done':
                    raise ValueError(f"Workflow for handover token {job['handover_token']} is already completed ")

                if spec['params']['status']:
                    if spec['params']['current_job'].get('job_id', False):
                        job_id = job.get('job_id', spec['params']['current_job']['job_id'])
                        host = spec['params']['current_job']['HOST']
                        status = stop_running_job(job_id, spec['params'], host)
                    else:
                        raise ValueError(f"Job not started : {spec['params']['current_job']['job_id']}  ")
                else:
                    raise ValueError(f"Workflow for handover token {job['handover_token']} is already stopped ")

                return jsonify(status)
                # return redirect(url_for('EventWorkflowJobStatus'))

        except Exception as e:
            return Response(str(e), status=400)


class EventWorkflowJobStatus(SwaggerView):
    parameters = [
        {
            "name": "release",
            "in": "path",
            "type": "string",
            "default": str(app.config['RELEASE'])
        },
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
    tags = ["Rapid Workflow job status"]
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
            release = request.args.get('release', str(app.config['RELEASE']))
            format = request.args.get('format', None)

            if format and format == 'json':
                return render_template('ensembl/qrp/list.html')

            with ElasticsearchConnectionManager(es_host, es_port, es_user, es_password, es_ssl) as es:
                jobs = []

                if handover_token:
                    res = es.client.search(index=es_index, body={
                        "size": 0,
                        "query": {
                            "bool": {
                                "must": [
                                    {"term": {"params.handover_token.keyword": str(handover_token)}},
                                    {"query_string": {"fields": ["report_type"], "query": "(INFO|ERROR)",
                                                      "analyze_wildcard": "true"}},
                                ]
                            }
                        },
                        "aggs": {
                            "top_result": {
                                "top_hits": {
                                    "size": 1,
                                    "sort": {
                                        "report_time": "desc"
                                    }
                                }
                            }
                        },
                        "sort": [
                            {
                                "report_time": {
                                    "order": "desc"
                                }
                            }
                        ]
                    })
                for doc in res['aggregations']['top_result']['hits']['hits']:
                    jobs.append(doc['_source'])

                else:
                    # res = es.search(index=es_index, body= {"size":300, "query": {"match_all": {}}})
                    res = es.search(index=es_index, body={
                        "size": 0,
                        "query": {
                            "bool": {
                                "must": [
                                    {
                                        "query_string": {
                                            "fields": [
                                                "report_type"
                                            ],
                                            "query": "(INFO|ERROR)",
                                            "analyze_wildcard": "true"
                                        }
                                    },
                                    {
                                        "query_string": {
                                            "fields": [
                                                "params.tgt_uri"
                                            ],
                                            "query": "/.*_{}(_[0-9]+)?/".format(release)
                                        }
                                    }
                                ]
                            }
                        },
                        "aggs": {
                            "handover_token": {
                                "terms": {
                                    "field": "params.handover_token.keyword",
                                    "size": 1000
                                },
                                "aggs": {
                                    "top_result": {
                                        "top_hits": {
                                            "size": 1,
                                            "sort": {
                                                "report_time": "desc"
                                            }
                                        }
                                    }
                                }
                            }
                        },
                        "sort": [
                            {
                                "report_time": {
                                    "order": "desc"
                                }
                            }
                        ]
                    })
                    for each_handover_bucket in res['aggregations']['handover_token']['buckets']:
                        for doc in each_handover_bucket['top_result']['hits']['hits']:
                            jobs.append(doc['_source'])

            return jsonify(jobs)
        except Exception as e:
            return Response(str(e), status=400)


class EventRecords(SwaggerView):
    tags = ["Insert/Update Event Records in ElasticSearch"]
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
            with ElasticsearchConnectionManager(es_host, es_port, es_user, es_password, es_ssl) as es:
                if json_pattern.match(request.headers['Content-Type']):
                    spec = request.json
                    res = es.client.index(index=es_index, doc_type='jobs', id=spec['handover_token'], body=spec)
                    return {'status': True, 'error': ''}
        except Exception as e:
            return Response(str(e), status=400)

        return {'status': True, 'error': ''}

    def put(self):
        """
        Update Event Record In ElasticSearch
        """
        try:
            with ElasticsearchConnectionManager(es_host, es_port, es_user, es_password, es_ssl) as es:
                if json_pattern.match(request.headers['Content-Type']):
                    spec = request.json
                    res = es.client.update(index=es_index, doc_type='jobs', id=spec['handover_token'], body={"doc": spec})
                    return {'status': True, 'error': ''}
        except Exception as e:
            return Response(str(e), status=400)


app.add_url_rule(
    '/workflows/submit',
    view_func=EventWorkflow.as_view('SubmitWorkflow'),
    methods=['POST']
)

app.add_url_rule(
    '/workflows/restart',
    view_func=EventRestartWorkflow.as_view('RestartWorkflow'),
    methods=['POST']
)

app.add_url_rule(
    '/workflows/stop',
    view_func=EventStopWorkflow.as_view('StopWorkflow'),
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

if __name__ == "__main__":
    app.run(debug=True)
