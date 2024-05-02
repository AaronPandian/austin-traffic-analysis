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

# Function definitions
def create_summary(jobid):
    """
    This function receives a job request and finds the average location of traffic
    incidents in the given timeframe.

    Args:
        jobid (string): Unique job ID

    Returns:
        summary (string): A summary statistics statement of the traffic 
                          incidents over the timeframe specified by the job.
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

def create_chart(jobid):
    """
    This function, based on the summary results, creates a bar chart of the
    charecteristics of observed incidents over the noted time period.

    Args:
        jobid (string): Unique job ID

    Returns:
        result (list): Array of information to create the chart.
    """
    job = get_job_by_id(jobid)
    start = job['start']
    end = job['end']
    incident_times = []
    incident_dates = []
    logging.debug('Worker read job data')
    start_date = date(int(start[6:10]), int(start[0:2]), int(start[3:5])) # Year(4)/Month(2)/Day(2) add space at end.
    end_date = date(int(end[6:10]), int(end[0:2]), int(end[3:5]))
    timeStep = 'year'
    duration = end_date.year-start_date.year
    if start_date.year==end_date.year:
        if start_date.month==end_date.month:
            if start_date.day==end_date.day:
                timeStep = 'hour'
            else:
                timeStep = 'day'
                duration = end_date.day-start_date.day
        else:
            timeStep = 'month'
            duration = end_date.month-start_date.month
    
    #making list of valid days and/or times depending on timestep
    for item in rd.keys():
        incident = json.loads(rd.get(item))
        #Check if data is valid (inside job timeframe)
        data_date = incident['Published Date']
        incident_date = date(int(data_date[6:10]), int(data_date[0:2]), int(data_date[3:5]))
        if (start_date <= incident_date and incident_date <= end_date):
            #Append data to list
            if timeStep == 'hour':
                incident_time = str(data_date[11:19]) #storing hh:mm:ss
                if str(data_date[20:23])=='PM':
                    incident_time[0:2] = str(int(incident_time[0:2])+12)
                incident_times.append(incident_time)
            else:
                incident_dates.append(incident_date)
    if timeStep=='hour':
        #Morning is defined as 6am-12pm, afternoon is 12pm-5pm (12-17 military time), evening is 5pm-10pm(17-22 military time), late_night is 10pm-6am (22-6military time). Notice that spread is 6hrs, 5hrs, 5hrs, then 8hrs. These are divided in unequal amounts on account of time periods of interest. 
        result = {'Morning':0, 'Afternoon':0, 'Evening':0, 'Late_night':0}
        #duration = max(incident_times)-min(incident_times)
        for item in incident_times:
            hr = int(item[0:2])
            mins = int(item[3:5])
            sec = int(item[6:8])
            if hr>=6 and hr<=12:
                if hr==12:
                    if (mins>0) or (sec>0):
                        result['Afternoon']+=1
                        continue
                result['Morning']+=1
                continue
            elif hr>12 and hr<=17:
                if hr==17:
                    if (mins>0) or (sec>0):
                        result['Evening']+=1
                        continue
                result['Afternoon']+=1
                continue
            #hr>17 or <6
            else: 
                result['Late_night']+=1
                continue
    else:
        result = []
        if timeStep == 'year':
            for i in range(duration+1):
                result.append({start_date.year+i:0})
            for item in incident_dates:
                for i in range(duration+1):
                    if (item.year-start_date.year)==i:
                        result[i][item.year]+=1
                        continue
        elif timeStep == 'month':
            for i in range(duration+1):
                result.append({start_date.month+i:0})
            for item in incident_dates:
                for i in range(duration+1):
                    if (item.month-start_date.month)==i:
                        result[i][item.month]+=1
                        continue
        else:
            for i in range(duration+1):
                result.append({start_date.day+i:0})
            for item in incident_dates:
                for i in range(duration+1):
                    if (item.day-start_date.day)==i:
                        result[i][item.day]+=1
                        continue
    return result

def create_map(jobid):
    """
    This function, based on the summary results, creates a map
    of the observed incidents over the noted time period

    Args:
        jobid (string): Unique job ID

    Returns:
        result (dictionary): Dictionary of lists with information to create
                             the incident map.
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

def create_regional_report(jobid):
    """
    This function, based on the time range provided, creates a summary report on the 
    incident data based on the region they occured in Austin.

    Args:
        jobid (string): Unique job ID

    Returns:
        report (dict): Summary report of the regional distribution of the 
                       incidents that occured during the timeframe specified
                       by the job.
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
        for index,lat in enumerate(incident_latitudes):
            if lat-Downtown_Austin[0] > 0.01:
                rel_lat[index] = 'North'
            elif lat-Downtown_Austin[0] < -0.01:
                rel_lat[index] = 'South'
        rel_lon = ['Same']*len(incident_longitudes)
        for index,lon in enumerate(incident_longitudes):
            if abs(lon)-abs(Downtown_Austin[1]) < -0.01:
                rel_lon[index] = 'East'
            elif abs(lon)-abs(Downtown_Austin[1]) > 0.01:
                rel_lon[index] = 'West'
        for index, lat in enumerate(rel_lat):
            lon = rel_lon[index]
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
    if (graph_request == 'yes'):
        incident_graph = create_chart(jobid)

    incident_report = 'Report not requested'
    if (report_request == 'yes'):
        incident_report = create_regional_report(jobid)
    

    # Finish the Job
    update_job_status(jobid, 'Complete')
    post_result(jobid, [summary, incident_map, incident_graph, incident_report])

do_work()
