"""
The flowing example is using the `asyncio` and `aiohttp` libraries in Python to make multiple asynchronous API requests to retrieve WHOIS information for a list of domains. 

1. `api_key` and `url`: The code uses `os.getenv()` to retrieve the value of the environment variable `WXAAPI` and assigns it to the `api_key` variable. The `url` variable 
holds the base URL for the WHOIS API, with placeholder values for the `api_key` and `domainName`.
2. `domains`: This is a list of domain names for which WHOIS information will be retrieved. You can add or remove domains from this list as needed.
3. `start` and `end` time: These variables are used to measure the elapsed time for the API calls.
4. `get_tasks()` function: This function creates a list of tasks using `asyncio.create_task()`. Each task represents an asynchronous HTTP GET request to the WHOIS API for a 
specific domain.
5. `get_domains()` coroutine: This is the main asynchronous function that will be run using `asyncio.run()`. It uses `aiohttp.ClientSession()` to create a session, calls 
`get_tasks()` to get the list of tasks, and then uses `asyncio.gather()` to await the completion of all the tasks.
6. `asyncio.set_event_loop_policy()`: This line sets the event loop policy specifically for Windows systems. It ensures that the code runs correctly on Windows platforms. 
If you're running the code on a different operating system, you can remove this line.
7. The `print()` statements at the end display the total time taken to make the API calls and indicate the completion of the task.
Overall, the code demonstrates how to use `asyncio` and `aiohttp` to efficiently make multiple asynchronous API requests. It allows you to fetch WHOIS information for multiple domains concurrently, 
reducing the overall execution time.
"""

import asyncio
import aiohttp
import os
import time
import platform

api_key = os.getenv('WXAAPI')
url = 'https://www.whoisxmlapi.com/whoisserver/WhoisService?apiKey={}&domainName={}&outputFormat=JSON'
domains = ['microsoft.com', 'google.com', 'apple.com', 'amazon.com', 'ebay.com', 'cisco.com', 'cnn.com', 'msnbc.com', 'foxnews.com', 'abcnews.com']

start = time.time()

def get_tasks(session):
    tasks = []
    for domain in domains:
        tasks.append(asyncio.create_task(session.get(url.format(domain, api_key), ssl=False)))
    return tasks

async def get_domains():
    async with aiohttp.ClientSession() as session:
        tasks = get_tasks(session)
        responses = await asyncio.gather(*tasks)

if platform.system() == 'Windows':
	asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

asyncio.run(get_domains())

end = time.time()
total_time = end - start
print("It took {} seconds to make {} API calls".format(total_time, len(domains)))
print('Task Complete')

# in this example, it took less than 0.4 seconds to do 10 WHOIS request.
