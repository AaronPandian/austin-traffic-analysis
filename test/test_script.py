#!/usr/bin/env python3

# Imports
import xmltodict
import logging
import requests
from api import app, handle_data, get_ids, get_id_data, submit_job, get_job, output_result
from jobs import get_result
import pytest
from flask import Flask, request

# Global variables / constants
app.testing = True
client = app.test_client()
# Class definitions

# Function definitions

# JOB FUNCTIONS   
""" 
def test_get_result(desired job id):
    # Testing how the get_result job function handles errors, depends on generated UUID.
    with pytest.raises(TypeError):
        get_dataset(desired job id) 
"""

# API FUNCTIONS
def test_handle_data(client):
    """
    Testing truths to validate the handle_data GET method funciton.
    """
    response = client.get('/data')
    datasetBytes = response.data
    dataset = datasetBytes.decode('utf8')
    assert isinstance(dataset, str) == True

def test_get_ids(client):
    """
    Testing truths to validate the get_ids funciton.
    """
    response = client.get('/ids')
    idsBytes = response.data
    ids = idsBytes.decode('utf8')
    assert isinstance(ids, str) == True

def test_submit_job(client):
    """
    Testing truths to validate the submit_job GET method funciton.
    """
    response = client.get('/ids/AEE6E7CBA08370F8E346C2A6268372C40BE71FB7_1548118671') 
    jobsBytes = response.data
    jobs = jobsBytes.decode('utf8')
    assert isinstance(jobs, str) == True

"""
def test_get_job(client):
    # Testing truths to validate the get_job funciton, depends on generated UUID
    response = client.get('/jobs/<insert generated id>')
    jobBytes = response.data
    job = jobBytes.decode('utf8')
    assert isinstance(jobs, str) == True

# WORKER FUNCTION
def test_output_result(client):
    # Testing truths to validate the output_result funciton, depends on generated UUID
    response = client.get('/results/<insert generated id>')
    resultBytes = response.data
    result = resultBytes.decode('utf8')
    assert isinstance(result, str) == True
"""

def unit_test():
    """
    Run all unit test functions.
    """
    # Job function tests
    test_get_result()

    # Route function tests
        # main check is to verify the route works, not the return
    test_handle_data(client=client)
    test_handle_data(client=client)
    test_get_ids(client=client)
    test_submit_job(client=client)
    #test_get_job(client=client)

    # Worker function test
    #test_output_result(client=client)

if __name__ == '__test_api__':
    unit_test()
