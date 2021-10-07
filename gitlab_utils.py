#!/usr/bin/python3
'''
Utility client for interacting with your gitlab instance.
'''

import base64
import json
import sys
import urllib.parse
from requests import Session
from requests.adapters import HTTPAdapter
from requests.packages.urllib3.util.retry import Retry

DORA_METRIC_LIST = ['deployment_frequency', 'lead_time_for_changes']

class TimeoutHTTPAdapter(HTTPAdapter):
    '''
    Represents a requests class that times out and backs off
    '''
    def __init__(self, *args, **kwargs):
        if "timeout" in kwargs:
            self.timeout = kwargs["timeout"]
            del kwargs["timeout"]
        super().__init__(*args, **kwargs)

    def send(self, request, **kwargs):
        timeout = kwargs.get("timeout")
        if timeout is None and hasattr(self, 'timeout'):
            kwargs["timeout"] = self.timeout
        return super().send(request, **kwargs)

class GitLabClient():
    '''
    Represents a connection to a GitLab Instance
    '''
    def __init__(self, url, token):
        '''
        Create the class
        '''
        self.url = url
        self.token = token
        retries = Retry(total=3, backoff_factor=1, status_forcelist=[429, 500, 502, 503, 504])
        self.http = Session()
        self.http.mount("https://", TimeoutHTTPAdapter(timeout=10, max_retries=retries))
        self.http.mount("http://", TimeoutHTTPAdapter(timeout=10, max_retries=retries))


    def check_gitlab_alive(self):
        '''
        check simple gitlab liveness
        '''
        status = False
        headers = {}
        headers['PRIVATE-TOKEN'] = self.token
        url = "{}/-/liveness".format(self.url)
        req = self.http.get(url, headers=headers, timeout=10)
        if req.ok:
            rval = json.loads(req.text)
            if rval == {"status":"ok"}:
                status = True
        return status


    def get_dora_metrics(self, group_project, prod_label, start_date):
        '''
        retrieve the daily dora metrics matching the start_date (yesterday)
        '''
        metrics = []
        project = urllib.parse.quote_plus(group_project)
        for metric in DORA_METRIC_LIST:
            endpoint = "projects/{}/dora/metrics?metric={}&start_date={}&environment_tier={}".format(
		        project, metric, start_date, prod_label)
            metric_results = self.query_gitlab(endpoint)
            for metric_result in metric_results:
                if metric_result.get('date') == start_date:
                    # correct metric
                    metric_result['project'] = group_project
                    metric_result['metric'] = metric
                    metrics.append(metric_result)
        return metrics

    def get_group_projects(self, group_prefix):
        '''
        Retrieve all projects under a given group/subgroup
	    (including all children's children)
        '''
        group = urllib.parse.quote_plus(group_prefix)
        endpoint = "groups/{}/projects?include_subgroups=true".format(group)
        return self.query_gitlab(endpoint)

    def get_json_file(self, project_id, filename, branch):
        '''
        Retrieve base64-encoded content file from gitlab
        '''
        file_object = None
        endpoint = "projects/{}/repository/files/{}?ref={}".format(project_id,
                                                                   filename,
                                                                   branch)
        content = self.query_gitlab(endpoint)
        try:
            if content.get('encoding') != 'base64':
                print("Error: unknown encoding - {}".format(content.get('encoding')))
            else:
                json_content = base64.b64decode(content.get('content'))
                file_object = json.loads(json_content)
        except TypeError:
            print("Error: Could not decode JSON content of file: {}".format(filename))
            sys.exit(1)
        return file_object

    def query_gitlab(self, endpoint):
        '''
        request endpoint from gitlab
        '''
        url = "{}/api/v4/{}".format(self.url, endpoint)
        headers = {}
        headers['PRIVATE-TOKEN'] = self.token
        response = self.http.get(url, headers=headers)
        if response.status_code == 404:
            return None
        if response.ok:
            if response.links.get('next'):
                return self.query_gitlab_paginated(response.text, response, headers)
            return json.loads(response.text)
        response.raise_for_status()
        sys.exit(1)

    def query_gitlab_paginated(self, existing, response, headers):
        '''
        request endpoint from gitlab with pagination
        '''
        results = json.loads(existing)
        while response.links.get('next'):
            url = response.links.get('next').get('url')
            response = self.http.get(url, headers=headers)
            if response.ok:
                results.extend(json.loads(response.text))
        return results

    def search_projects(self, group_prefix):
        '''
        search projects from gitlab
        '''
        search_term=urllib.parse.quote_plus(group_prefix)
        endpoint = "search?scope=project&search={}".format(search_term)
        return self.query_gitlab(endpoint)
