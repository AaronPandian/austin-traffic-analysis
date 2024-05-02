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
import plotly.express as px
import pandas as pd

# Global variables / constants
log_var = os.environ.get('LOG_LEVEL', 'DEBUG') # set in docker-compose
logging.basicConfig(level=log_var)
#job_id = ""

# Function definitions
#@q.worker
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
    #job_id = jobid
    job = get_job_by_id(jobid)
    start = job['start']
    end = job['end']
    incident_latitudes = []
    incident_longitudes = []
    logging.debug('Worker read job data')
    start_date = date(int(start[6:10]), int(start[0:2]), int(start[3:5])) # Year(4)/Month(2)/Day(2) add space at end.
    end_date = date(int(end[6:10]), int(end[0:2]), int(end[3:5]))
    try:
        # Gather the average location of all incidents within timeframe
        for item in rd.keys():
            incident = json.loads(rd.get(item)) # Gets incident dictionary
            # Create check between timeframe
            data_date = incident['Published Date']
            incident_date = date(int(data_date[6:10]), int(data_date[0:2]), int(data_date[3:5]))
            #start_date = date(int(start[6:10]), int(start[0:2]), int(start[3:5])) # Year(4)/Month(2)/Day(2) add space at end.
            if (start_date <= incident_date and incident_date <= end_date):
                # Append the locations to the lists
                incident_latitudes.append(float(incident['Latitude']))
                incident_longitudes.append(float(incident['Longitude']))
        logging.debug('Worker finished analysis')
        lonavg = sum(incident_longitudes)/len(incident_longitudes)
        latavg = sum(incident_latitudes)/len(incident_latitudes)
        freq = len(incident_latitudes)
        summary = f"The average incident location is at ({latavg}N, {lonavg}W), and there were {freq} incidents during this period.\n"
        return summary
    except TypeError:
        logging.warning('Worker could not initialize dates correctly')
        post_result(jobid, 'Data processing was unsuccessful')
        update_job_status(jobid, 'Complete')
        return "Failed to process data, check if data and job parameters were posted correctly\n"
    """    
    logging.info('Worker finished job')
    lonavg = sum(incident_longitudes)/len(incident_longitudes)
    latavg = sum(incident_latitudes)/len(incident_latitudes)
    freq = len(incident_latitudes)
    summary = f"The average incident location is at ({latavg}N, {lonavg}W), and there were {freq} incidents during this period."
    logging.info('Worker compiled the summary')
    return summary
    """

#@q.worker
def create_chart(jobid):
    """
    This function, based on the summary results, creates a bar chart of the charecteristics
    of observed incidents over the noted time period.

    Args:
        jobid (string): Unique job ID

    Returns:
        result (list): Array of information to create the chart.
    """

#@q.worker
def create_map(jobid):
    """
    This function, based on the summary results, creates a map
    of the observed incidents over the noted time period

    Args:
        jobid (string): Unique job ID

    Returns:
        result (dictionary): Dictionary of lists with information to create the chart.
    """
    job = get_job_by_id(jobid)
    start = job['start']
    end = job['end']
    incident_latitudes = []
    incident_longitudes = []
    incident_addresses = []
    logging.debug('Worker read job data')
    start_date = date(int(start[6:10]), int(start[0:2]), int(start[3:5])) # Year(4)/Month(2)/Day(2) add space at end.
    end_date = date(int(end[6:10]), int(end[0:2]), int(end[3:5]))
    try:
        for item in rd.keys():
            incident = json.loads(rd.get(item))
            #Check if data is valid (inside job timeframe)
            data_date = incident['Published Date']
            incident_date = date(int(data_date[6:10]), int(data_date[0:2]), int(data_date[3:5]))
            if (start_date <= incident_date and incident_date <= end_date):
                #Append data to list
                incident_latitudes.append(float(incident['Latitude']))
                incident_longitudes.append(float(incident['Longitude']))
                incident_addresses.append(str(incident['Address']))
        logging.debug('Worker finished analysis')
        result = {'latitudes':incident_latitudes, 'longitudes': incident_longitudes, 'Address': incident_addresses}
        return result 
    except TypeError:
        logging.warning('Worker could not initialize dates correctly')
        post_result(jobid, 'Data processing was unsuccessful')
        update_job_status(jobid, 'Complete')
        return 

#@q.worker
def create_regional_report(jobid):
    """
    This function, based on the time range provided, creates a summary report on the 
    incident data based on the region they occured in Austin.

    Args:
        jobid (string): Unique job ID

    Returns:
        result (list): Summary report in list format.
    """
    job = get_job_by_id(jobid)
    start = job['start']
    end = job['end']
    incident_latitudes = []
    incident_longitudes = []
    Downtown_Austin = [30.2672, -97.7431] # N, W; lat, long
    cDowntown = 0 #count of incidients in downtown, +- 0.01 degrees in either direction
    cEast = 0 
    cWest = 0
    cNorth = 0
    cSouth = 0
    cNE = 0
    cNW = 0
    cSW = 0
    cSE = 0
    logging.debug('Worker read job data')
    start_date = date(int(start[6:10]), int(start[0:2]), int(start[3:5])) # Year(4)/Month(2)/Day(2) add space at end.
    end_date = date(int(end[6:10]), int(end[0:2]), int(end[3:5]))
    try:
        for item in rd.keys():
            incident = json.loads(rd.get(item))
            #Check if data is valid (inside job timeframe)
            data_date = incident['Published Date']
            incident_date = date(int(data_date[6:10]), int(data_date[0:2]), int(data_date[3:5]))
            if (start_date <= incident_date and incident_date <= end_date):
                #Append data to list
                incident_latitudes.append(float(incident['Latitude']))
                incident_longitudes.append(float(incident['Longitude']))
        rel_lat = ['Same']*len(incident_latitudes)
        for i in range(len(incident_latitudes)):
            if incident_latitudes[i]-Downtown_Austin[0] > 0.01:
                rel_lat[i] = 'North'
            elif incident_latitudes[i]-Downtown_Austin[0] < 0.01:
                rel_lat[i] = 'South'
        rel_lon = ['Same']*len(incident_longitudes)
        for i in range(len(incident_longitudes)):
            if incident_longitudes[i]-Downtown_Austin[1] > 0.01:
                rel_lon[i] = 'East'
            elif incident_latitudes[i]-Downtown_Austin[1] < 0.01:
                rel_lon[i] = 'West'
        for lat in rel_lat:
            for lon in rel_lon:
                if (lat=='Same') and (lon=='Same'):
                    cDowntown+=1
                elif lat=='North':
                    if lon=='Same':
                        cNorth+=1
                    elif lon=='East':
                        cNE+=1
                    else:
                        cNW+=1
                elif lat=='South':
                    if lon=='Same':
                        cSouth+=1
                    elif lon=='East':
                        cSE+=1
                    else:
                        cSW+=1
                else:
                    if lon=='East':
                        cEast+=1
                    else:
                        cWest+=1
        logging.debug('Worker finished analysis')
        report = {'Downtown':cDowntown, 'North': cNorth, 'NE':cNE, 'NW':cNW, 'East': cEast, 'West': cWest, 'South':cSouth, 'SW':cSW, 'SE':cSE}
        return report
    except TypeError:
        logging.warning('Worker could not initialize dates correctly')
        post_result(jobid, 'Data processing was unsuccessful')
        update_job_status(jobid, 'Complete')
        return

@q.worker
def do_work(jobid):
    # Main function definition
    update_job_status(jobid, 'In Progress')
    logging.info('Worker starting work')
    
    # Initiate analysis
    job = get_job_by_id(jobid)
    map_request = job['incident_map']
    graph_request = job['incident_graph']
    report_request = job['incident_report']

    # Run the summary regardless
    summary = create_summary(jobid)
    
    
    # Run checks for the other data
    incident_map = 'Map not requested'
    if (map_request == 'yes'):
        incident_map = create_map(jobid)

    incident_graph = 'Graph not requested'
    #if (graph_request == 'yes'):
    #    incident_graph = create_graph(jobid)

    incident_report = 'Report not requested'
    if (report_request == 'yes'):
        incident_report = create_regional_report(jobid)
    

    # Finish the Job
    update_job_status(jobid, 'Complete')
    post_result(jobid, [summary, incident_map, incident_graph, incident_report])

do_work()
