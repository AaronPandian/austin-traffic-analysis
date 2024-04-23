#!/usr/bin/env python3

import json
import uuid
import redis
from hotqueue import HotQueue
import logging
import os

_redis_ip='redis-db'
_redis_port='6379'

rd = redis.Redis(host=_redis_ip, port=6379, db=0)
q = HotQueue("queue", host=_redis_ip, port=6379, db=1)
jdb = redis.Redis(host=_redis_ip, port=6379, db=2)
results = redis.Redis(host=_redis_ip, port=6379, db=3)

env_var = os.environ.get('REDIS_IP', _redis_ip)
log_var = os.environ.get('LOG_LEVEL', 'DEBUG') # set in docker-compose
logging.basicConfig(level=log_var)

def _generate_jid():
    """
    Generate a pseudo-random identifier for a job.
    """
    logging.info('Generating new job ID')
    return str(uuid.uuid4())

def _instantiate_job(jid, status, start, end):
    """
    Create the job object description as a python dictionary. Requires the job id,
    status, start and end parameters.
    """
    logging.info('Formatting new job')
    return {'id': jid,
            'status': status,
            'start': start,
            'end': end }

def _save_job(jid, job_dict):
    """Save a job object in the Redis database."""
    jdb.set(jid, json.dumps(job_dict))
    return

def _queue_job(jid):
    """Add a job to the redis queue."""
    q.put(jid)
    return

def add_job(start, end, status="submitted"):
    """Add a job to the redis queue."""
    logging.info('Adding new job to queue')
    jid = _generate_jid()
    job_dict = _instantiate_job(jid, status, start, end)
    _save_job(jid, job_dict)
    _queue_job(jid)
    return job_dict

def get_job_by_id(jid):
    """Return job dictionary given jid"""
    logging.info('Getting job ID from database')
    return json.loads(jdb.get(jid))

def get_job_ids():
    """Returns all job ids"""
    logging.info('Getting all job IDs from database')
    return_value = []
    for item in jdb.keys():
        return_value.append(json.loads(jdb.get(item)))
    logging.debug('Successfully parsed through job database')
    return return_value

def update_job_status(jid, status):
    """Update the status of job with job id `jid` to status `status`."""
    logging.info('Updating job status')
    job_dict = get_job_by_id(jid)
    if job_dict:
        job_dict['status'] = status
        _save_job(jid, job_dict)
    else:
        logging.warning('Problem reading the job status')
        raise Exception()

def post_result(jid, result):
    """Sends result to results database"""
    logging.info('Posting job result to redis database')
    results.set(jid, json.dumps(result))
    return 

def get_result(jid):
    """Receives result from results database"""
    logging.info('Getting job result from redis database')
    return json.loads(results.get(jid))
