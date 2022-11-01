
import sys
sys.path.append('/home/karthika/Desktop/PhishMesh/PhishMeshCrawler/')
sys.path.append('/home/karthika/Desktop/PhishMesh/data/')

from openphish_config import *
from database import phish_db_layer, phish_db_schema


import boto3
import json
import time
import asyncio
from datetime import datetime, timezone

class OpenPhishFeeds:
    def __init__(self):
        self.aws_access_key = AWS_ACCESS_KEY_ID
        self.aws_secret_access_key = AWS_SECRET_ACCESS_KEY


    async def record_openphish_urls(self, file_path):
        openphish_urls = {}
        with open(file_path, 'r') as fj:
            openphish_urls = json.load(fj)
        print('recording urls ::', len(openphish_urls))

        for url_det in openphish_urls:
            # print(url_det)
            try:
                open_phish_obj = phish_db_schema.Open_Phish_Links(open_phish_url = url_det["url"],
                                    open_phish_sector = url_det["sector"],
                                    open_phish_screenshot = url_det["screenshot"],
                                    open_phish_phishkit = url_det["phishing_kit"],
                                    open_phish_brand = url_det["brand"],
                                    discover_time = datetime.strptime(url_det["discover_time"], "%d-%m-%Y %H:%M:%S %Z").replace(tzinfo=timezone.utc).astimezone(tz=None)
                                    )
                phish_db_layer.add_open_phish_link(open_phish_obj)
            except Exception as e:
                print(e)

    async def fetch_open_phish_feeds(self):
        while True:
            try:
                c = boto3.client(
                            's3',
                            aws_access_key_id = self.aws_access_key,
                            aws_secret_access_key = self.aws_secret_access_key
                        )
                file_name = "{}-feed.json".format(datetime.today().strftime('%d%m%Y_%H:%M'))
                print('Writing Feed to file --> '+ file_name)
                file_name = '../data/openphish_feeds_new/'+ file_name
                with open( file_name, 'wb') as local_feed:
                    c.download_fileobj('opfeeds', 'premium_plus/feed.json', local_feed)
                
                ### record urls to database
                asyncio.ensure_future(self.record_openphish_urls(file_name))
            except Exception as e:                
                print(e)    
                exit()
            ### wait for 10 mins to fetch next feed
            await asyncio.sleep(600)

    def start(self):
        loop = asyncio.get_event_loop()        
        task = loop.create_task(self.fetch_open_phish_feeds())

        try:
            loop.run_until_complete(task)
        except asyncio.CancelledError:
            pass



if __name__ == "__main__":
    opf_obj = OpenPhishFeeds()
    opf_obj.start()
