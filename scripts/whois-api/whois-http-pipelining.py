# WHOISXMLAPI.COM
# HTTP Pipelining example v1.0
# 

import requests

def send_pipelined_requests(host, paths):
    
    with requests.Session() as session:
        
        # Send multiple requests in a pipelined manner
        responses = [session.get(f"https://{host}{path}") for path in paths]

        for response, path in zip(responses, paths):
            rh = response.headers.get('content-type')
            if 'application/json' in rh:
                json_data = response.json()
                print("-" * 40)
                print("Registered domainName:",json_data['WhoisRecord']['domainName'])
                print("Registrar Name:", json_data['WhoisRecord']['registrarName'])
                print("IANAID:", json_data['WhoisRecord']['registrarIANAID'])
                print("Created:",json_data['WhoisRecord']['createdDate'])
                print("Updated:",json_data['WhoisRecord']['updatedDate'])
                print("Expires:",json_data['WhoisRecord']['expiresDate'])
                print("Estimated Domain Age:", json_data['WhoisRecord']['estimatedDomainAge'])
            else:
                print("Unexpected content-type returned:", rh)

if __name__ == "__main__":

    submitWHOIS = []

    # set your API Key 
    apiKey = "at_********************"
    target_host = "whoisxmlapi.com"
    uri = "/whoisserver/WhoisService?apiKey=" + apiKey  + "&outputFormat=JSON" + "&domainName="

    domainNames = [ "google.com", "apple.com", "microsoft.com", "paypal.com", "amazon.com" ]

    for dn in domainNames:
        fmtURL = uri + dn
        submitWHOIS.append(fmtURL)

    send_pipelined_requests(target_host, submitWHOIS)
