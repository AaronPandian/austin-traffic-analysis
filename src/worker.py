#!/usr/bin/env python3

# Imports
from jobs import get_job_by_id, update_job_status, post_result, q, rd # Methods and clients
from hotqueue import HotQueue
import redis
import time
from datetime import date, timedelta
import json
import os
import logging

# Global variables / constants
log_var = os.environ.get('LOG_LEVEL', 'DEBUG') # set in docker-compose
logging.basicConfig(level=log_var)

# Function definitions
@q.worker
def create_summary(jobid):
    """
    This function receives a job request and finds the average location of traffic
    incidents in the given timeframe.

    Args:
        jobid (string): Unique job ID

    Returns:
        result (list): Summary statement in list format.
    """

    # Initiate analysis
    job = get_job_by_id(jobid)
    start = job['start']
    end = job['end']
    incident_latitudes = []
    incident_longitudes = []
    logging.debug('Worker read job data')

    try:
        # Gather the average location of all incidents within timeframe
        for item in rd.keys():
            incident = json.loads(rd.get(item)) # Gets incident dictionary
            # Create check between timeframe
            data_date = incident['Published Date']
            incident_date = date(int(data_date[6:10]), int(data_date[0:2]), int(data_date[3:5]))
            start_date = date(int(start[6:10]), int(start[0:2]), int(start[3:5])) # Year(4)/Month(2)/Day(2) add space at end.
            end_date = date(int(end[6:10]), int(end[0:2]), int(end[3:5]))
            if (start_date <= incident_date and incident_date <= end_date):
                # Append the locations to the lists
                incident_latitudes.append(float(incident['Latitude']))
                incident_longitudes.append(float(incident['Longitude']))
        logging.debug('Worker finished analysis')
    except TypeError:
        logging.warning('Worker could not initialize dates correctly')
        post_result(jobid, 'Data processing was unsuccessful')
        update_job_status(jobid, 'Complete')
        return
        
    logging.info('Worker finished job')
    lonavg = sum(incident_longitudes)/len(incident_longitudes)
    latavg = sum(incident_latitudes)/len(incident_latitudes)
    freq = len(incident_latitudes)
    summary = f"The average incident location is at ({latavg}N, {lonavg}W), and there were {freq} incidents during this period."
    logging.info('Worker compiled the summary')
    return summary

@q.worker
def create_chart(jobid):
    """
    This function, based on the summary results, creates a bar chart of the charecteristics
    of observed incidents over the noted time period.

    Args:
        jobid (string): Unique job ID

    Returns:
        result (list): Array of information to create the chart.
    """

@q.worker
def create_map(jobid):
    """
    This function, based on the summary results, creates a map
    of the observed incidents over the noted time period

    Args:
        jobid (string): Unique job ID

    Returns:
        result (list): Array of information to create the chart.
    """

@q.worker
def create_regional_report(jobid):
    """
    This function, based on the time range provided, creates a summary report on the 
    incident data based on the region they occured in Austin.

    Args:
        jobid (string): Unique job ID

    Returns:
        result (list): Summary report in list format.
    """

# Main function definition
update_job_status(jobid, 'In Progress')
logging.info('Worker starting work')

# Initiate analysis
job = get_job_by_id(jobid)
map_request = job['incident_map']
graph_request = job['incident_graph']
report_request = job['incident_report']

# Run the summary regardless
summary = create_summary()

# Run checks for the other data
incident_map = 'Map not requested'
if (map_request == 'yes'):
    incident_map = create_map(jobid)

incident_graph = 'Graph not requested'
if (graph_request == 'yes'):
    incident_graph = create_graph(jobid)

incident_report = 'Report not requested'
if (report_request == 'yes'):
    incident_report = create_regional_report(jobid)

# Finish the Job
update_job_status(jobid, 'Complete')
post_result(jobid, [summary, austin_map, graph, report])
