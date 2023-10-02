# rename to lambda_function.py
#
import os
import boto3
import sys
from datetime import datetime, timedelta
sys.path.append('python') #added for requests module
import requests
from requests.auth import HTTPBasicAuth


def lambda_handler(event, context):
    # Calculate yesterday's date in YYYY-MM-DD format
    yesterday = (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d")

    # Define the URL of the CSV file you want to download
    csv_url = f"https://emailverification.whoisxmlapi.com/datafeeds/Disposable_Email_Domains/disposable-emails.full.{yesterday}.txt"

    # Define your API key here from Whoisxmlapi.com
    apiKey = "YOUR_API_KEY"

    # Define the username and password for basic authentication
    username = apiKey
    password = apiKey

    # Define the S3 bucket and object/key where you want to store the CSV
    "s3://newbucketname/email/disposable/"
    s3_bucket = "newbucket"
    s3_key = f"email/disposable/disposable-email-domains-{yesterday}.csv"

    # Initialize the S3 client
    s3_client = boto3.resource('s3')
    s3_object = s3_client.Object(s3_bucket, s3_key)
    
    try:
        # Download the CSV file from the external website with basic authentication
        response = requests.get(csv_url, auth=HTTPBasicAuth(username, password))
        
        print("Status code returned is ", str(response.status_code))

        if response.status_code == 200:
            # Upload the CSV file to S3
            print(f"Uploading file to ", s3_bucket, s3_key)
            s3_object.put(Body=response.content)
            return {
                'statusCode': 200,
                'body': 'CSV file successfully downloaded and uploaded to S3'
            }
        else:
            bodyStr = f"Failed to download {csv_url}"
            return {
                'statusCode': response.status_code,
                'body': bodyStr
            }
    except Exception as e:
        return {
            'statusCode': 500,
            'body': str(e)
        }
