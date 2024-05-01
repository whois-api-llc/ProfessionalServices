# monitorapis.py

import requests
import json
import logging

url = 'https://main.whoisxmlapi.com/api-status.json'

def discordWebhook(apiStr):

    # example

     webhook_url = 'https://discord.com/api/webhooks/************************'

     payload = {
         'username': 'WHOISAPIBOT',
         'content': apiStr
     }

     response = requests.post(webhook_url, json=payload)

logging.basicConfig(
            level=logging.DEBUG,  # Set the logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
            )

# Setup logging facility 
logger = logging.getLogger("WHOISAPIBOT")
# set the path is other than local directory
log_file = 'whoisapibot.log'
file_handler = logging.FileHandler(log_file)
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
file_handler.setFormatter(formatter)
logger.addHandler(file_handler)

try:
    response = requests.get(url)

    logStr = "APIMON Run, Response code = " + str(response.status_code)
    logger.debug(logStr)

    if response.status_code == 200:
        json_data = response.json()

        for x in range(len(json_data)):
             apiName = json_data[x]['name']
             apiStatus = json_data[x]['status']
             apiTime = json_data[x]['responseTime']

             if apiStatus >= 0:
                  if apiStatus == 1:
                       apiMessage = "The partial outage status means the API did not pass some of our internal tests."
                  elif apiStatus == 2:
                       apiMessage = "The data returned can be outdated, incomplete or missing."
                  elif apiStatus == 3:
                       apiMessage = "Major outage - all test failed."
                  elif apiStatus == 0:
                       apiMessage = "Passed"
                  else:
                       apiMessage = "Unknown value " + str(apiStatus)

                  apiStr = "[API] " + apiName + ",[status] " + apiMessage

                  #debug
                  #print(apiStr)

                  # log every message unless otherwise instructed to
                  logger.info(apiStr)
                  #discordWebhook(apiStr)
    else:
        apiStr = "Failed to load JSON data. Status code: " + str(response.status_code)
        logger.critical(apiStr)
        discordWebhook(apiStr)

except requests.exceptions.RequestException as e:
    apiStr = "Error occured: " + e
    logger.critical(apiStr)
    discordWebhook(apiStr)
