import os
import requests

# Set colors (ANSI escape codes)
red_text = '\x1b[31m'
green_text = '\x1b[32m'
yellow_text = '\x1b[33m'
reset_color = '\x1b[0m'

print("Downloading Threat Intel data from whoisxmlapi.com")
print("Contact sales@whoisxmlapi.com for more information.")

# Define the list of files to download. Modify the list to match your use case.
tidf_file_names = [
    "deny-cidrs.v4",
    "deny-cidrs.v6",
    "deny-domains",
    "deny-ips.v4",
    "deny-ips.v6",
    "hosts",
    "malicious-cidrs.v4.csv",
    "malicious-cidrs.v4.jsonl",
    "malicious-cidrs.v6.csv",
    "malicious-cidrs.v6.jsonl",
    "malicious-domains.csv",
    "malicious-domains.jsonl",
    "malicious-file-hashes.csv",
    "malicious-file-hashes.jsonl",
    "malicious-ips.v4.csv",
    "malicious-ips.v6.csv",
    "malicious-ips.v4.jsonl",
    "malicious-ips.v6.jsonl",
    "malicious-urls.csv",
    "malicious-urls.jsonl",
    "nginx-access.v4",
    "nginx-access.v6",
]

# Define the base URL where the WXA Threat Intel files are located
base_url = "https://threat-intelligence.whoisxmlapi.com/datafeeds/Threat_Intelligence_Data_Feeds/"

# Manually define the WHOISXMLAPI.COM API Key
api_key = "<YOUR_API_KEY>"
# Better to define it in an environment variable
# api_key = os.getenv("WXAAPIKEY")

# Specify the local path where you want to save the downloaded zip file
local_path = "C:/TEMP"  # Use forward slashes (/) or double backslashes (\\) for Windows paths

# Get the current date in the desired format (YYYY-MM-DD)
from datetime import datetime, timedelta

yesterday = datetime.now() - timedelta(days=1)
formatted_date = yesterday.strftime("%Y-%m-%d")

print(f"Preparing to download {len(tidf_file_names)} files for {formatted_date}")

iteration_count = 0

for tdif_file_name in tidf_file_names:
    iteration_count += 1

    # Construct the URL for tdif.YYYY-MM-DD.daily.
    tdif_get_file = f"tidf.{formatted_date}.daily.{tdif_file_name}.gz"
    complete_uri = base_url + tdif_get_file

    # Create the full local path for the zip file
    local_file_path = os.path.join(local_path, tdif_get_file)

    try:
        print(f"{yellow_text} {iteration_count} ... Downloading {tdif_get_file} file to: {local_file_path}{reset_color}")
        headers = {"Authorization": f"Basic {api_key}:{api_key}"}
        response = requests.get(complete_uri, headers=headers)

        if response.status_code == 200:
            with open(local_file_path, "wb") as file:
                file.write(response.content)
            print(f"{green_text}  Success{reset_color}")
        else:
            print(f"{red_text}  An error occurred while downloading the {tdif_get_file} file{reset_color}")
            print(f"{red_text}  Error details: {response.status_code}{reset_color}")
    except Exception as e:
        print(f"{red_text}  An error occurred while downloading the {tdif_get_file} file{reset_color}")
        print(f"{red_text}  Error details: {str(e)}{reset_color}")

print("All files downloaded successfully")
