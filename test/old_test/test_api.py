import pytest
import requests

response1 = requests.get('http://127.0.0.1:5000/data')
response2 = requests.get('http://127.0.0.1:5000/genes')
test_gid = 'HGNC:5'
response3 = requests.get('http://127.0.0.1:5000/genes/'+test_gid)
response4 = requests.get('http://127.0.0.1:5000/jobs')
#test_job = {'hgnc_id1':'HGNC:5', 'hgnc_id2':'HGNC:19255'}
#response5 = requests.post(config.tool_repo_urls['http://127.0.0.1:5000/jobs'], data = json.dumps(test_job), headers={'Content-Type': 'application/json'})


def test_data_route_get_method():
    assert response1.status_code == 200
    assert isinstance(response1.json(), list) == True

def test_genes_route():
    assert response2.status_code == 200
    assert isinstance(response2.json(), list) == True

def test_specific_genes_route():
    assert response3.status_code == 200
    assert isinstance(response3.json(), dict) == True

def test_jobs_route():
    assert response4.status_code == 200
    assert isinstance(response4.json(), dict) == True
    #assert response5.status_code == 200
    #assert isinstance(response5.json(), str) == True


