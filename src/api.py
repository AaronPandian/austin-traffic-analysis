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
        result (string): Statement mentioning the POST request has been 
                         completed.
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
        result[0] (string): A summary statement of the traffic incidents 
                            between the specified job timeframe. 
        result_map (string): A statement with directions on how to download
                             the computed map image to a local working 
                             directory.
        result_chart (string): A statement with directions on how to 
                               download the computed chart image to a local
                               working directory.
        result_report(string): A report statement of the regional 
                               distribution of the traffic incidents in the
                               specified job timeframe. 
        
    """
    logging.info('Getting job results from seperate redis database')
    job = get_job_by_id(jobid)
    status = job['status']
    logging.debug('Job status received')
    if (status == 'Complete'):
        result = get_result(jobid)
        result_map_test = result[1]
        result_chart_test = result[2]
        result_report_test = result[3]
        #Checking if a map was requested, if so make one
        if result_map_test != 'Map not requested':
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
                result_map = f'Find incident map by copying from container using this command: "docker cp <insert continer ID for api>:{map_path} <path to desired local folder, use \'.\' if the current local working directory is the designated location>" \n'
            except Exception as e:
                print("Error when saving map to directory:", e)
                logging.error('Failed to save image\n')
        else:
            result_report = result_report_test

        if result_chart_test != 'Graph not requested':
        #make chart
            result_chart = ''

        #Checking if a report was requested, if so make one
        if result_report_test != 'Report not requested':
            logging.debug('Making incident report\n')
            result_report =  f'This is the accident distribution for each region of austin(in the format of \'Region\': <#incidents>):\n {result_report_test}\nNote that downtown is defined as 30.2672 N (+- 0.01 degrees), -97.7431 W (+-0.01 degrees). Also note that the other regions are relative to downtown. For example, \'North\' Austin is 30.2772 N (or greater), and -97.7431 W (+-0.01 degrees).\n'
        else:
            result_report = result_report_test
        #Compile the computed results into neat output with standardized format
        return f'{result[0]} \n {result_map} \n{result_report}\n'
    else:
        logging.warning('The job has not finished yet')
        return 'Your data is still being analyzed and calculated\n'

@app.route('/help', methods=["GET"])
def help():
    """
    This is a function that provides a string with short descriptions of 
    each route and it's usages.

    Args:
        None

    Returns:
        help_str (string): A brief summary with short descriptions of each 
                           api route and its usage. 
    """
    general_info = "Note that for all the route endpoints, they build off of the base url (either 'localhost:5000/' or 'http://127.0.0.1:5000/'). As such, for a route, say '/data', the final url to curl could be 'localhost:5000/data' plus the desired method.\n"
    route1 = "The '/data' route has 'GET', 'POST', and 'DELETE' methods that can be used to load in the data, view the loaded data, and delete the data from the redis database server\n"
    route2 = "The '/ids' route has a 'GET' method that is used to list all of the unique traffic incident report IDs. If the information for a specific traffic id is desired, it can be viewed by querying the desired id to the end, like so for example <desired_id>: '/ids/<desired_id>'.\n"
    route3 = "The '/jobs' route has 'POST' and 'GET' methods to post a job request and view the details of all exisiting job requests respetively. Note that if a specific job ID's details are desired, they can be queried with a 'GET' method. For example, with an example job id of <ex_job_id>, the specifics for this job id can be displayed with '/jobs/<ex_job_id>'.\n"
    route4 = "The '/results/<desired_id>' route has a 'GET' method that attmepts to compute results for a desired job id, <desired_id>, then displays these results. Note that if a chart or map is requested, it will be saved to the container on which the app is run, and can later be retrieved with a docker cp request (if on linux) to download to the local working directory.\n"
    help_str = f'{general_info}\n{route1}\n{route2}\n{route3}\n{route4}\n' 
    return help_str

# Main function definition

# Run Flask
if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
