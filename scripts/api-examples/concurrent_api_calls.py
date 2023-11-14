# Concurrent API call Example  v1.0   October 14, 2023
# Sends 100 API calls and awaits for response before sending another 100
# WHOISXMLAPI.COM - Professional Services.  Developer: Mengchen Qu
# This example code is provided as is and without any type of warranty.
# Input is a single column list of domain names to look up WHOIS records.

import aiohttp
import asyncio
import pandas as pd
import csv
from tqdm import tqdm
import json
import os

async def fetch(session, url, retry=3):
    for i in range(retry):
        try:
            async with session.get(url) as response:
                if response.status == 200:
                    return await response.text()
                else:
                    response.raise_for_status()
        except aiohttp.ClientResponseError as e:
            if e.status == 429:  
                await asyncio.sleep(10)  
            else:
                raise  
    return None  

async def fetch_all(session, urls):
    tasks = [asyncio.create_task(fetch(session, url)) for url in urls]
    results = await asyncio.gather(*tasks)
    return results

def extract_data(api_responses):
    data = []
    for response in api_responses:
        json_response = json.loads(response)
        whois_record = json_response.get('WhoisRecord', {})
        registry_data = whois_record.get('registryData', {})
        domain_name = whois_record.get('domainName', '')
        created_date = registry_data.get('createdDate', '')
        registrant_email = whois_record.get('contactEmail', '')
        
        data.append([domain_name, created_date, registrant_email])
    return data

async def main():
    # get domains from csv file
    df = pd.read_csv('/Users/sunnyqu/Desktop/t1000.csv', header=None, usecols=[0])
    domains = df[0].tolist()
    print(domains)

    # API Key and Endpoint - obtain from env or define manually
    api_key = os.getenv('WHOISAPIKEY')
    api_endpoint = 'https://www.whoisxmlapi.com/whoisserver/WhoisService'

    # ClientSession
    async with aiohttp.ClientSession() as session:
        # CSV and csvwriter
        with open('/Users/sunnyqu/Desktop/result.csv', 'w', newline='') as csvfile:
            csvwriter = csv.writer(csvfile)
            csvwriter.writerow(['Domain Name', 'Creation Date', 'Registrant'])

            # 100 * 10
            for i in tqdm(range(0, len(domains), 100)):
                    batch = domains[i:i+100]
                    urls = [f'{api_endpoint}?apiKey={api_key}&domainName={domain}&outputFormat=JSON' for domain in batch]
                    responses = await fetch_all(session, urls)
                    data = extract_data(responses)
                    print("Writing data to CSV:", data)
                    csvwriter.writerows(data)
                    print("----------------------------------Data successfully written to CSV.-------------------------------------")
                    await asyncio.sleep(5) 
                    print(f"---------Batch {i} processed--------------")

if __name__ == '__main__':
    asyncio.run(main())
