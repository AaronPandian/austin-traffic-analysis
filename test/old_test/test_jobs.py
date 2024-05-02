import pytest
import os
import json
import redis
from hotqueue import HotQueue

_redis_ip = os.environ.get('REDIS_IP')

rd = redis.Redis(host=_redis_ip, port=6379, db=0)
q = HotQueue("queue", host = _redis_ip, port = 6379, db = 1)
jdb = redis.Redis(host=_redis_ip, port = 6379, db = 2)

from ..src.jobs import add_job, get_job_by_id

test_gid1 = 'HGNC:5'
test_gid2 = 'HGNC:19255'

def test_jobs():
    assert isinstance(add_job(test_gid1, test_gid2, status="submitted").json(), dict) == True
    assert isinstance(get_job_by_id(add_job(test_gid1, test_gid2, status="submitted").json()).json(), dict) == True


