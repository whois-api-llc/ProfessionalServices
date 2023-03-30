try:
    #python3
    from urllib.request import Request, urlopen, pathname2url
except ImportError:
    #python2
    from urllib import pathname2url
    from urllib2 import urlopen
import sys
import json

productID = []
productName = []
productCredits = []
sendWebhooks = []
productWarning = 90
total_products = 0

def calc_percentage(part, whole):

    if part >= whole:
        return 0.0
    else:
        return 100 - ((part/whole) * 100)

def load_account_balances(result):

    global total_products

    for x in result['data']:
        productID.append(x['product_id'])
        productName.append(x['product']['name'])
        productCredits.append(x['credits'])
        sendWebhooks.append(0)
        total_products += 1

def check_balances():
    global total_products
    percent = 0.0

    # Write the output in CSV format to stdout

    print("\tid,prod_name,credits_remaining,account_credits,balance,percent_remaining,signal")

    for x in range(total_products):
        match productID[x]:
            case 1:
                total_credits = 1000000000
            case 7:
                total_credits = 3000
            case 8:
                total_credits = 1000
            case 14:
                total_credits = 2000
            case 20:
                total_credits = 3000
            case 21:
                total_credits = 2000
            case 23:
                total_credits = 100
            # Add/Remove cases as desired to match products your interested in
            case default:
                total_credits = 500

        remaining_credits = total_credits - productCredits[x]

        percent = round(calc_percentage(productCredits[x],total_credits))

        if remaining_credits < 0:
            result = "negative"
            sendWebhooks[x] = 1
        elif remaining_credits == 0:
            result = "exhausted"
            sendWebhooks[x] = 1
        else:
            result = "positive"

        print(f"\t{productID[x]},{productName[x]},{productCredits[x]},{total_credits},{remaining_credits},{percent},{result}")

def generate_webhooks():

    total_sent = 0

    # Insert your favorite webhook code

    for x in range(total_products):
        if sendWebhooks[x] == 1:
            total_sent += 1

    return total_sent

if __name__ == "__main__":

    # recommend using api_key = os.getenv('WHOISAPIKEY') or some other method instead of hard coding it
    # for simplicity, its hard coded here
    api_key = '<YOUR_API_KEY>'

    balance_url = 'https://user.whoisxmlapi.com/user-service/account-balance'
    uri = balance_url + '?apiKey=' + api_key
    req = Request(uri, headers={"User-Agent": "Mozilla/5.0"})

    print("Connecting to:", balance_url)

    try:
        result = json.loads(urlopen(req).read())
    except:
        print("Failed to read API")
        sys.exit(-1)

    load_account_balances(result)

    # Idea: write to json results to file based on date to run time usage analysis

    print("\tCompleted. Total products read from API: ", total_products, "\nLoading product definitions")

    print("\tGenerating CSV output:\n")

    check_balances()

    print("Done. Generating Webhooks...")

    print("\tTotal Webhooks sent... ",generate_webhooks())

    print("\nProcess Complete")
