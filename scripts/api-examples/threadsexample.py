# WHOISXMLAPI.COM  2024

import requests
import time
from concurrent.futures import ThreadPoolExecutor, as_completed

def send_request(url):

    try:
        response = requests.get(url)
        return response.status_code
    except requests.exceptions.RequestException as e:
        return str(e)

def main(url, rate_limit, per_second):

    counter = 0

    max_concurrent_requests = rate_limit
    
    time_frame = per_second

    with ThreadPoolExecutor(max_workers=max_concurrent_requests) as executor:
        while True:
            start_time = time.time()

            futures = [executor.submit(send_request, url) for _ in range(rate_limit)]
            
            for future in as_completed(futures):
                status = future.result()
                counter += 1
                print(f'{counter}: status: {status}')

            elapsed_time = time.time() - start_time

            if elapsed_time < time_frame:
                   time.sleep(time_frame - elapsed_time)

if __name__ == "__main__":
 
    endpoint = 'https://www.whoisxmlapi.com/whoisserver/WhoisService?apiKey='
    apiKey = 'YOUR_API_KEY'
    domainName = 'google.com'
    rate_limit = 30
    per_second = 5

    target_url = endpoint + apiKey + "&" + "domainName=" + domainName
    main(target_url, rate_limit, per_second)
