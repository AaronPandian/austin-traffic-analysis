#!/usr/bin/env python3

# Imports
import requests
from flask import Flask, request
import numpy as np
import redis
import json
import csv
from jobs import add_job, get_job_by_id, get_job_ids, get_result
import os
import logging
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
#from io import StringIO

# Global variables/constants
app = Flask(__name__)
rd = redis.Redis(host='redis-db', port=6379, db=0)

log_var = os.environ.get('LOG_LEVEL', 'DEBUG') # set in docker-compose
logging.basicConfig(level=log_var)

# Function definitions
@app.route('/data', methods=['GET', 'POST', 'DELETE'])
def handle_data():
    """
    This function conudcts the main post, get, and delete methods on the
    traffic incedent data.

    Returns: (only one of the two return types are ouput)
        result (string): For post and delete requests, a string is sent 
        noting the request has been completed.
        result_value (list): A list of all the traffic incidents within
        the dataset.
    """
    if request.method == 'POST':
        logging.info('Accessing data from database')
        # Get the genome data from the website, use the CSV file with times
        response = requests.get("https://data.austintexas.gov/api/views/dx9v-zd7x/rows.csv?accessType=DOWNLOAD")
        # Create CSV dictionary as JSON format
        data = {}
        data['traffic_data'] = [] 
        open('data.csv', 'wb').write(response.content)
        with open('data.csv', 'r') as f:
            reader = csv.DictReader(f)
            for row in reader:
                data['traffic_data'].append(dict(row))
        logging.debug('Success reading dataset')
        # Iterate over the data to store in redis
        for item in data['traffic_data']:
            rd.set(item['Traffic Report ID'], json.dumps(item)) # Item at index one of datapoint is ID number
        logging.debug('Success inputting data into redis')
        # Return response
        os.remove("data.csv")
        return "The POST request is completed\n"

    elif request.method == 'GET':
        return_value = []
        logging.info('Reading all data from redis')
        # Iterate over keys in redis
        for item in rd.keys():
            return_value.append(json.loads(rd.get(item)))
        # Return everything as a JSON object
        return return_value

    elif request.method == 'DELETE':
        # Delete everything in redis
        logging.info('Deleting data from redis')
        for item in rd.keys():
            rd.delete(item)
        # Return response
        return "The DELETE request is completed\n"
    else:
        logging.warning('Invalid specified method.')

@app.route('/ids', methods=['GET'])
def get_ids():
    logging.info('Getting all data from redis')
    """
    This function gets all the unique IDs of posted traffic incedents.

    Returns:
        result (list): List of unique IDs of traffic incedents. 
    """
    return_value = []
    # Iterate over keys in redis
    for item in rd.keys():
    # Append the keys
        value = return_value.append(item.decode('utf8'))
    # Return everything as a JSON object
    return return_value

"""
test queried route: 

@app.route('/ids?offset&limit', methods=['GET'])
def queried_get_ids():
"""

@app.route('/ids/<desired_id>', methods=['GET'])
def get_id_data(desired_id):
    logging.info('Getting specified data from redis')
    """
    This function gets data of a specific traffic incident.

    Args:
        desired_id (string): Unique traffic incedent ID.

    Returns:
        result (list): A list dictionary of the traffic incident requested. 
    """
    return_value = []
    # Iterate over keys in redis
    for item in rd.keys():
        # Check if specified key
        if desired_id == item.decode('utf8'):
            return_value.append(json.loads(rd.get(item)))
    # Return response once found
    return return_value

@app.route('/jobs', methods=['POST', 'GET'])
def submit_job():
    """
    This function conducts the main post and get methods on the user
    requested jobs.

    Returns: (only one of the two return types are ouput)
        result (string): Statement mentioning the POST request has been completed.
        result (list): List of all the unique job IDs in the queue. 

    """
    if request.method == 'POST':
        logging.info('Posting job to seperate redis database')
        data = request.get_json()
        # Set parameters to be the start and end dates
        job_dict = add_job(data['start'], data['end'], data['incident_map'], data['incident_graph'], data['incident_report'])
        return 'POST request completed for desired job.\n'
    elif request.method == 'GET':
        logging.info('Getting all data from seperate redis database')
        return get_job_ids()
    else:
        logging.warning('Invalid specified method.')

@app.route('/jobs/<jobid>', methods=['GET'])
def get_job(jobid):
    """
    This function provides information on a specific job ID.

    Args:
        jobid (string): Unique job ID.

    Returns:
        result (list): A list dictionary of the specific job requested. 
    """
    logging.info('Getting job from seperate redis database')
    return [get_job_by_id(jobid)]

@app.route('/results/<jobid>', methods=['GET'])
def output_result(jobid):
    """
    This function provides the result of a job.

    Args:
        jobid (string): Unique job ID.

    Returns: (only one of the two return types are ouput)
        result (string): A status statement.  
        result (list): A summary statement of the traffic incidents between 
        the specified job timeframe. 
    """
    logging.info('Getting job results from seperate redis database')
    job = get_job_by_id(jobid)
    status = job['status']
    logging.debug('Job status received')
    if (status == 'Complete'):
        result = get_result(jobid)
        result_map = result[1]
        result_report = result[3]
        # Instead of return result, return the list of all information and create output from results here $$$$$$$$$$$$$$$$$$$$$
        if result_map != 'Map not requested':
            logging.debug('Attempting to make map\n')
            df = pd.DataFrame(result[1])
            fig = go.Figure()

            fig.add_trace(go.Scattermapbox(lon = df['longitudes'], lat = df['latitudes'],text = df['Address'], mode = 'markers', marker = go.scattermapbox.Marker(size = 8)))

            fig.update_layout(title = 'Austin Traffic Incident Map', geo_scope='usa', mapbox_style='open-street-map', mapbox_center={'lat':30.2672, 'lon':-97.7431},mapbox_zoom=10 )
            fig.update_geos(center=dict(lon=-97.7431, lat=30.2672), projection_scale=10, scope='usa')
            try: 
                logging.debug('Attempting to save map\n')
                curr_dir = os.path.abspath(os.getcwd())
                filename = 'Austin_Incident_Map.png'
                map_path = os.path.join(curr_dir, filename)
                fig.write_image(map_path, width=800, height=600, scale=2)
                logging.debug('Image saved\n')
                result_map = 'Find incident map by copying from container using this command: "docker cp <insert continer ID for api>:{map_path} <path to desired local folder, use \'.\' if the current local working directory is the designated location>" \n'
            except Exception as e:
                print("Error when saving map to directory:", e)
                logging.error('Failed to save image\n')
        if result_report != 'Report not requested':
            result_report =  f'This is the accident distribution for each region of austin(in the format of \'Region\': <#incidents>):\n {result[2]}'
        return f'{result[0]} \n {result_map} {result_report}\n'
    else:
        logging.warning('The job has not finished yet')
        return 'Your data is still being analyzed and calculated\n'

    # Create specific app route that gets the results, takes the image (graph and map) data, then downloads the images $$$$$$$$$$$$$$$$$$

# Main function definition

# Run Flask
if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
