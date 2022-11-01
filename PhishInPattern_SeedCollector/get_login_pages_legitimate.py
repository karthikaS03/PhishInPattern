import json
import os 
from pprint import pprint
import requests
import csv
import time

# Add your Bing Search V7 subscription key and endpoint to your environment variables.
subscription_key = 'dd3cf79e42f04360b8a7603e3c543fc6'
endpoint = 'https://api.bing.microsoft.com' + "/v7.0/search"


def get_login_urls():

    top_sites_file = '../data/alexa_urls.csv'
    if '.csv' in top_sites_file:     
        with open(top_sites_file) as cf:
            csvreader = csv.DictReader(cf, delimiter=',')
            i = 0
            for row in csvreader:        
                id = row['id']
                url = row['url']  
                query = url.replace('https://', '') + ' login page'   
                if int(id) > 90: 
                    urls = search_bing(query)      
                       
                    with open('../data/alexa_urls_login.csv','a+') as f:
                        for u in urls:
                            f.write(str(id)+','+u+'\n')
                time.sleep(2)  
                i=i+1
                if i>1000:
                    break


def search_bing(query ):
    # Construct a request
    mkt = 'en-US'
    params = { 'q': query, 'mkt': mkt }
    headers = { 'Ocp-Apim-Subscription-Key': subscription_key }
    urls = []
    # Call the API
    try:
        response = requests.get(endpoint, headers=headers, params=params)
        response.raise_for_status()

        print("\nJSON Response:\n")
        response_json = response.json()
        if 'webPages' in response_json:
            for res in response_json['webPages']['value']:
                # print(res)
                urls.append(res['url'])

        # pprint(response_json)
        pprint(urls)

    except Exception as ex:
        raise ex
    return urls 

get_login_urls()