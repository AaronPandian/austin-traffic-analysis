# REST API Analysis of Traffic Incident Data using Redis

## High-Level Description
### Project
Published by the local government of Austin are traffic incidents compiled by the Combined Transportation, Emergency, and Communications Center (CTECC). The data is primarily segmented into the location of occurrence, date and time of the incident, the type of report, and the filing agency. In this project, traffic information is populated into a Redis database through a Flask interface to enable in-depth data analysis for a user to conduct. Further capability is provided by job scheduling to allow the user to request analyses that require greater compiling time. This application is encapsulated within Kubernetes which allows the user to conduct said data-analysis in various environments. 

### Files
This folder contains a **Dockerfile** and **requirements.txt** file, which holds library dependencies of the code. Furthermore, the **docker-compose.yaml** file provides a swift method to build the necessary images. The source code folder consists of a main script **api.py** hosting the web application functions- returning analytical information from the traffic incident dataset online. This code utilizes the **jobs.py** and **worker.py** files to run job requests that indicate more complex, lengthy data analysis. A test folder holding the unit test script **test_script.py** provides a method to ensure the core functions work as they should. Lastly, the **kubernetes** directory holds the code in two folders, one for testing **test** and one for normal use case **prod**. The files of each variation are the same- but allow different use cases for the user. The specific code is described in more detail in the video, linked in the next section. 

## Diagram Overview
![Alt text](https://github.com/AaronPandian/austin-traffic-analysis/blob/main/SoftwareDiagram.png)

This software diagram presents a visual of the concurrency and relationship between the files in this repository and what they interact with that may be "hidden." A video overview can be found [here](https://drive.google.com/file/d/1HFKby_BCe3egJKaeDhe4eF7cqHsCfR9M/view?usp=sharing).

## About and Access to the Data
The traffic incident data this code requests can be found on the [Government Data Website](https://catalog.data.gov/dataset/real-time-traffic-incident-reports/resource/e9a86b8c-2b7f-4921-8f25-cfdac2202f2a). The data is stated to be updated every five minutes and is provided in JSON, CSV, XML, and RDF file formats- as seen on the website. In addition, the history of the reports dates back to November 12, 2020. The government has posted [summary statistics](https://data.austintexas.gov/stories/s/48n7-m3me) of their own and a [map of the reports](https://data.austintexas.gov/stories/s/Austin-Travis-County-Traffic-Report-Page/9qfg-4swh/). This will be used as a reference but will not be used for our data analysis.

The specific CSV traffic data referenced can be found [here](https://data.austintexas.gov/api/views/dx9v-zd7x/rows.csv?accessType=DOWNLOAD). The format of the dataset starts with metadata. For the actual data, each row entry in the CSV represents a new incident indicated with a unique Traffic ID. The parameters of each incident are as follows: Traffic Report ID, Published Date, Issue Reported, Location, Latitude, Longitude, Address, Status, Status Date, and Agency.

## Deploying Application on Local Hardware
First, ensure the environment you are using has Docker installed, and make sure the working directory has given Redis permissions.

### Container Build Preparation
Create a folder in your directory to input the code found in this folder by running `mkdir traffic_app`. 

Run `cd traffic_app` to enter the created folder then run the `git clone https://github.com/AaronPandian/austin-traffic-analysis.git` command to import all the files from this repository into your working directory. All the files should be in this folder. In this **traffic_app** directory run `mkdir data` to create a sub-directory for Redis **only if** the empty data folder from this directory did not build or if it is causing problems. 

Once all the files are gathered, double-check with `ls`.  

### How to Deploy Containerized Code as a Flask App
To create and run an image container, enter the command `docker-compose up -d --build` within the **traffic_app** directory. This runs the Docker Compose file which deploys the image in the background. 

Check if the build was successful with `docker images` or `docker ps -a`. You should see the three containers running, two with the tag `<dockerhubusername>/traffic_api:1.0` and the third labeled `redis:7`.

At this point, your container is running the main Python scripts in the terminal background. You can use the following section to interact with the application. 

Once you are done running the Flask app remove the image using the container ID found when running `docker images`. To do this, run `docker stop <containerID>` to stop the application from running in the background, then `docker rm <containerID>` to remove the instance from your list of containers.

## How to Build the Application using K8 Cluster
Expanding on the prior method, follow the steps to run the image- make sure three images are running using `docker ps -a`. From the **traffic_app** run `cd kubernetes` to enter the Kubernetes set-up directory. From here we will run a string of commands. In order, run the following.
```
kubectl apply -f traffic-prod-pvc-redis.yml
kubectl apply -f traffic-prod-service-redis.yml
kubectl get services
```
Copy the IP address from the Redis service and paste it into both the Flask and worker deployment scripts (**traffic-prod-deployment-flask.yml** **traffic-prod-deployment-worker.yml**) for the environment variable REDIS_IP value. Ensure quotation marks, like the placeholder IP address surround the IP address. After saving these updates, continue running the commands in order. 
```
kubectl apply -f traffic-prod-service-flask.yml
kubectl apply -f traffic-prod-deployment-flask.yml
kubectl apply -f traffic-prod-deployment-redis.yml
kubectl apply -f traffic-prod-deployment-worker.yml
kubectl apply -f traffic-prod-service-nodeport-flask.yml
kubectl apply -f traffic-prod-ingress-flask.yml
```
With each command, a print statement "completed" will deem a successful run. Once the cluster is in place and all three pods are running, you can verify using `kubectl get pods`, run `kubectl get ingress`. This will provide a specialized link from which you can call the application routes from a **public** endpoint. Copy this link and use it as the `<URL>` for curling the routes below. 

It is important to note that the post and get requests for the entire dataset take a long time and can sometimes cause a Gateway Time-out. As a result, before you run the `kubectl apply -f traffic-prod-ingress-flask.yml` from the steps above, run `kubectl get services` to get the unique port number from the generated nodeport (can look like this 5000:32627/TCP where the 32627 is the number we want). Copy the port number and run `curl -X POST coe332.tacc.cloud:<port number>/data` to post the traffic incident data to Redis. Conduct longer routes like this if they give you trouble in the preceding steps with the public URL. After conducting this, generate the public URL by running the ingress file for application use elsewhere. 

## Accessing Routes
Once the image is running, the terminal will wait for requests to be made using specific URL routes. Using the provided URL, paste the URL and append the following routes at the end of the URL to obtain the desired functions. 

* A POST request to `/data` loads the traffic data to a Redis database.
    * The command will look like `curl -X POST <URL>/data`.
* A GET request to `/data` should return all populated data from the Redis database as a JSON list.
    * The command will look like `curl -X GET <URL>/data`.
* A DELETE request to `/data` should delete all data from the Redis database.
    * The command will look like `curl -X DELETE <URL>/data`.
* `/ids` returns a JSON-formatted list of all the Traffic Incident IDs.
* `/ids/"<desired_id>"` route should return all data associated with a given `<desired_id>`.
    * Be sure to surround the id with quotation marks, like above.  

Additionally, the following commands can run job requests for more intensive operations. 

* A POST request to `/jobs` queues a new job with a unique ID. The worker script will then return summary statistics for traffic incidents between a specified date range. 
    * The command will look like `curl <URL>/jobs -X POST -d '{"start":"01/15/2022", "end":"01/15/2022","incident_map":"yes","incident_graph":"yes","incident_report":"yes"}' -H "Content-Type: application/json"`. The string date range is denoted within the curly brackets. 
    * The job **must** be formatted by issuing a start date that occurs before the end date. Furthermore, the format of dates **must** match the example command- days and months are 2 digits (i.e. 01, 15, 12), and years are 4 digits (i.e. 2021, 2023, 2024), separated by some character. Dates should not be before November 2020 or after the present day, since that is the expanse of the dataset. 
* A GET request to `/jobs` returns a list of all queued job IDs.
    * The command will look like `curl <URL>/jobs`.
* `/jobs/<jobid>` returns the job information for a specific job ID.
    * The command will look like `curl <URL>/jobs/<jobid>`.
 
To view results from a requested job use the following route.

* `/results/<jobid>` returns the analysis if the job is complete, if not it prompts the user to wait. 

## Output and What to Expect
In running the application and calling the routes above, the user should receive the respective information printed out to the terminal. If images are generated, instructions to view them are displayed as well. Some example commands are shown below.

##### `curl -X POST localhost:5000/data`
```
["The POST request is completed"]
```
##### `curl localhost:5000/ids`
Here, the output is a large list- shortened for this example. 
```
[ . . . 
  "7A1B52FD835B0BEBB79168905903AD903FDA01BF_1554142822",
  "69F2D00A2F210DDCB106C399671CF92C4F2A154A_1563212112",
  "A238EFA1E6BE785257FFA83915DC0E6EF13B355C_1641932492",
  "F2AB78F5097F975794065615DC6F9DA887CDA3C0_1645299236",
  "06BC6A372C0484BD4C62494038CAC7C4C62035DF_1573265498",
  "817965431C04A46F3AF2F982CEFF704A9CD0890B_1539693659",
  "80CB5A19FE9C8F7B1DFB602B6CE549E3B82A3DBF_1666991027",
  "0C4E6389BA7066F691E6C5AAA754C167FBB870F8_1605905286",
  "ADD97DAEFA483805F4A52716BA886AC2D97841B3_1653719549",
  "1A2D9204B47A686C709C7FB4D9CE3C6106935D7B_1520068684000",
  "9FD21EC59A17B645ADE7B1E56DA753BD45E19A2C_1596934316",
  "2BE753B3FFFF9B04B02C6D41A7A29067B1F86C02_1660322708",
  "CB852047223EB4C0EC2C483D9268EFB97861128A_1708380518",
  "FF9BB9F4C63520A6D11F97C33B576438879F887F",
  "C20DDEFA2174FFEC6DDB31D7E6D7DFB8B3F5C04C_1542327080",
  "A42763A9BA7A399B7F9738F5B9B41BEC5A94E87D_1684258800",
  "62F65D222E45D9E913A5D06D114F275B6A926CC7_1547661564",
  "00F36866326DA3B8DDE0D960226DCD6AFB5AF127_1601585023",
  "3EF7538B0F216C80090141B725F27B3D0767A38C_1698548907",
  "08BABBA456D31986A0E6B7A77F63A6D11CC82FC3_1571326614",
  "0CE1D1D8CFA8BDADD7BC865D3E87BBF2FBBC003E_1605974248",
  "A02EA72E938587C06DFE620416DDC0BC5B086887_1666783286",
  "DB5976F7596FB6AB160829C7D28336559C9C0AB2_1529785677",
  "CCF5CC6E320C9D0DC5B405AFA2289BF1BD040E74_1536259577",
  "9304739C29A855AF7DDB1CFC420CB7CF57726E00_1557090610",
  "397D13D9AEE3CE3572A22022F4C50CF8553A668A_1665966813",
  "AEE6E7CBA08370F8E346C2A6268372C40BE71FB7_1548118671"
]
```
##### `curl localhost:5000/ids/AEE6E7CBA08370F8E346C2A6268372C40BE71FB7_1548118671`
```
[
  {
    "Address": "N Mopac Expy Svrd Nb & W Braker Ln",
    "Agency": "",
    "Issue Reported": "Traffic Hazard",
    "Latitude": "30.395462",
    "Location": "POINT (-97.73208 30.395462)",
    "Longitude": "-97.73208",
    "Published Date": "01/22/2019 12:57:51 AM +0000",
    "Status": "ARCHIVED",
    "Status Date": "01/22/2019 01:25:03 AM +0000",
    "Traffic Report ID": "AEE6E7CBA08370F8E346C2A6268372C40BE71FB7_1548118671"
  }
]
```
##### `curl localhost:5000/jobs -X POST -d '{"start":"01/15/2022", "end":"01/15/2022","incident_map":"yes","incident_graph":"yes","incident_report":"yes"}' -H "Content-Type: application/json"`
```
{
  "end": "01/15/2022",
  "id": "c76b37b2-250d-4894-afe5-6d81d7c8475a",
  "incident_map": "yes",
  "incident_graph": "yes",
  "incident_report": "yes",
  "start": "01/15/2022",
  "status": "submitted"
}
```
##### `curl localhost:5000/jobs/c76b37b2-250d-4894-afe5-6d81d7c8475a`
```
{
  "end": "01/15/2022",
  "id": "c76b37b2-250d-4894-afe5-6d81d7c8475a",
  "incident_map": "yes",
  "incident_graph": "yes",
  "incident_report": "yes",
  "start": "01/15/2022",
  "status": "submitted"
}
```
##### `curl localhost:5000/results/c76b37b2-250d-4894-afe5-6d81d7c8475a`
```
The average incident location is at (30.313467875739622N, -97.73633102366863W), and there were 169 incidents during this period.

Find incident chart by copying from container using this command: "docker cp <insert container ID for api>:/app/Incident_Chart.png <path to desired local folder, use '.' if the current local working directory is the designated location>"

Find incident map by copying from container using this command: "docker cp <insert container ID for api>:/app/Austin_Incident_Map.png <path to desired local folder, use '.' if the current local working directory is the designated location>"

This is the accident distribution for each region of Austin (in the format of 'Region': <#incidents>):
 {'Downtown': 9, 'North': 6, 'NE': 62, 'NW': 30, 'East': 2, 'West': 3, 'South': 6, 'SW': 30, 'SE': 21}

Downtown is defined as 30.2672 N (+- 0.01 degrees), -97.7431 W (+-0.01 degrees). The other regions are relative to downtown. For example, 'North' Austin is 30.2772 N (or greater), and -97.7431 W (+-0.01 degrees).
```
For this output, the job request was posted to request a report, chart, and map. Also, to view the chart and map, simply download the graphic from the app container to the local directory of interest following the instructions from the output. May need to use 'docker ps -a' first to see the container ID for the API (not the worker or Redis), which will be needed to docker cp the image on Linux. Also note that for the chart image, the x-axis label is "Date/Time" as it is relative to the queried job timeframe (over several years, if the start and end year are the same then over months of that year if the start and end year and month are the same then over the days in that month; otherwise if the start and end year, month, and day are the same, over the time (hours) of that day.

##### `curl localhost:5000/help`
```
Note that for all the route endpoints, they build off of the base URL (either 'localhost:5000/' or 'http://127.0.0.1:5000/'). As such, for a route, say '/data', the final URL to curl could be 'localhost:5000/data' plus the desired method.

The '/data' route has 'GET', 'POST', and 'DELETE' methods that can be used to load the data, view the loaded data, and delete the data from the Redis database server

The '/ids' route has a 'GET' method that is used to list all of the unique traffic incident report IDs. If the information for a specific traffic ID is desired, it can be viewed by querying the desired id to the end, like so, for example, <desired_id>: '/ids/<desired_id>'.

The '/jobs' route has 'POST' and 'GET' methods to post a job request and view the details of all existing job requests respectively. Note that if a specific job ID's details are desired, they can be queried with a 'GET' method. For example, with an example job id of <ex_job_id>, the specifics for this job id can be displayed with '/jobs/<ex_job_id>'.

The '/results/<desired_id>' route has a 'GET' method that attempts to compute results for a desired job id, <desired_id>, then displays these results. Note that if a chart or map is requested, it will be saved to the container on which the app is run, and can later be retrieved with a docker cp request (if on Linux) to download to the local working directory.
```


