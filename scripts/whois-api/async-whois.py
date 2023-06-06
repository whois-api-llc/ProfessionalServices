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
