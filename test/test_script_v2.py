#!/usr/bin/env python3

# Imports
import xmltodict
import logging
import requests
from api import app, handle_data, get_ids, get_id_data, submit_job, get_job, output_result
from jobs import get_result, add_job, get_job_by_id, get_job_ids
import pytest
import redis
from flask import Flask, request
from hotqueue import HotQueue
import json
from worker import do_work

# Global variables / constants
#app.testing = True
#client = app.test_client()

_redis_ip = os.environ.get('REDIS_IP')

rd = redis.Redis(host=_redis_ip, port=6379, db=0)
q = HotQueue("queue", host = _redis_ip, port = 6379, db = 1)
jdb = redis.Redis(host=_redis_ip, port = 6379, db = 2)

start = '01/15/2022'
end = '01/15/2022'

response1 = request.post('http://127.0.0.1:5000/data')
response2 = request.get('http://127.0.0.1:5000/data')
response3 = request.get('http://127.0.0.1:5000/ids')
repsonse4 = request.post('http://127.0.0.1:5000/jobs', data = {start, end, no, no ,no})
response6 = request.get('http://127.0.0.1:5000/help')
# Class definitions

# Function definitions

# JOB FUNCTIONS   
def test_jobs():
    assert isinstance(add_job(start, end, no, no, no, status="submitted").json(), dict) == True
    assert isinstance(get_job_by_id(add_job(start, end, no, no, no, status="submitted").json()).json(), dict) == True
    assert isinstance(get_job_by_id(add_job(test_gid1, test_gid2, status="submitted").json()).json(), dict) == True
    assert isinstance(get_job_ids(), list) == True
    test_jid = get_job_ids()[0]
    assert isinstance(get_result(test_jid), dict) == True
    
# API FUNCTIONS
def test_handle_data():
    """
    Testing truths to validate the handle_data GET method funciton.
    """
    #response = client.get('/data')
    assert response1.status_code == 200
    assert response2.status_code == 200
    assert isinstance(response1.data.decode('utf8'), str) == True
    datasetBytes = response2.data
    dataset = datasetBytes.decode('utf8')
    assert isinstance(dataset, str) == True

def test_get_ids():
    """
    Testing truths to validate the get_ids funciton.
    """
    #response = client.get('/ids')
    assert response3.status_code == 200
    assert isinstance(reponse3.data.decode('utf'), list) == True
    test_id = response3.json()[0]
    #idsBytes = response.data
    #ids = idsBytes.decode('utf8')
    #assert isinstance(ids, str) == True
    assert isinstance(get_id_data(test_id), list)== True

"""
def test_submit_job(client):
 
    #Testing truths to validate the submit_job GET method funciton.

    #response = client.get('/ids/AEE6E7CBA08370F8E346C2A6268372C40BE71FB7_1548118671') 
    #jobsBytes = response.data
    #jobs = jobsBytes.decode('utf8')
    #assert isinstance(jobs, str) == True
"""

def test_get_job():
    # Testing truths to validate the get_job funciton, depends on generated UUID
    #response = client.get('/jobs/<insert generated id>')
    #jobBytes = response.data
    #job = jobBytes.decode('utf8')
    #assert isinstance(jobs, str) == True
    assert response4.status_code == 200
    assert isinstance(response4.data.decode('utf8'), str or list)==True
    test_jid = get_job_ids()[0]
    assert isinstance(get_job(test_jid), list)==True

def test_output_result():
    # Testing truths to validate the output_result funciton, depends on generated UUID
    #response = client.get('/results/<insert generated id>')
    #resultBytes = response.data
    #result = resultBytes.decode('utf8')
    #assert isinstance(result, str) == True
    test_jid = get_job_ids()[0]
    response5 = request.get('http://127.0.0.1:5000/results/'+test_jid)
    assert response5.status_code == 200
    assert isinstance(response5.data.decode('utf8'), str)==True
    
def test_help():
    assert response6.status_code == 200
    assert isinstance(response6.data.decode('utf8'), str) ==True
    
#Test Worker functionality
def test_worker():
    assert(isinstance(do_work(test_jid)), None) == True

def unit_test():
    """
    Run all unit test functions.
    """
    # Job function tests
    #test_get_result()
    test_jobs()
    # Route function tests
        # main check is to verify the route works, not the return
    """
    test_handle_data(client=client)
    test_handle_data(client=client)
    test_get_ids(client=client)
    test_submit_job(client=client)
    test_output_result()
    test_help()

    """
    test_handle_data()
    test_get_ids()
    test_get_job()

    #test_get_job(client=client)

    # Worker function test
    #test_output_result(client=client)
    test_worker()

if __name__ == '__test_api__':
    unit_test()
