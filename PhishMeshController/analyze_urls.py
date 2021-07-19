 
import pandas as pd 
import concurrent.futures
import docker
import time
import datetime
import os
import json 
import sys
sys.path.append("../SWSec_Analysis/database")

import db_operations

# from docker_config import *
from docker_monitor import *

# import logging




# logging.basicConfig(filename='output_new.log', filemode='w', format='%(name)s - %(levelname)s - %(message)s',level=logging.INFO)

client = docker.from_env()
dbo = db_operations.DBOperator()

container_timeout = 300
urls_path = '' 
max_containers = 10
id_prefix = ''
iteration_count =0

def set_config():
	global container_timeout
	global urls_path 
	global max_containers
	global id_prefix
	global iteration_count

	if CRAWL_SW ==True:
		container_timeout = CRAWL_TIMEOUT
		urls_path = CRAWL_URL_PATH
		max_containers = CRAWL_MAX_CONTAINERS
		id_prefix = 'Seed_Alexa_'
		iteration_count = 0
		
	else:
		container_timeout = ANALYSIS_TIMEOUT
		urls_path = ANALYSIS_URL_PATH
		max_containers = ANALYSIS_MAX_CONTAINERS
		id_prefix = 'Mal_' if IS_MALICIOUS else 'Seed_Alexa_Ana_'
		iteration_count = 0
		

def process_urls_parallel(analysis_urls, script_file, cont_timeout, max_cont):
	futures={}
	processed_url_ids = set()
	urls = analysis_urls.copy()
	with concurrent.futures.ProcessPoolExecutor(max_workers = max_cont) as executor:
		while len(urls)>0:
			## Submit jobs to container ##
			for i in range(min(len(urls),max_cont)):
				id = urls.keys()[0]
				itm = urls.pop(id)
				url = itm['url']
				# print(url)
				visit_count = itm['count']
				if i!=0 and i%3==0:
					time.sleep(120)
				if visit_count==0:
					## initiates docker container for the first time
					futures[executor.submit(initiate_container, url, str(id), script_file, visit_count, cont_timeout)] = (str(id),visit_count, url)		
				else:
					## Resumes docker container and waits for notifications
					futures[executor.submit(resume_container,url, str(id), script_file, visit_count, cont_timeout)] = (str(id), visit_count, url)	
			
			try:
				##  Keep docker container active for specific duration and stop the containe and export data 
				print('waiting for containers to complete execution')
				# print(futures)
				for future in  concurrent.futures.as_completed(futures, timeout=cont_timeout):
					id, v_count, url = futures.pop(future)				
					try:
						get_logger('container_'+id).info(get_time() + 'Container_'+ str(id) +': Completed successfully!!'	)	
					except concurrent.futures.TimeoutError as ex:
						get_logger('container_'+id).info(get_time() +  'Container_' + str(id) +': Timeout occured!!')
					except Exception as exc:
						get_logger('container_'+id).info(get_time() +  'Container_' + str(id) +': Exception ')
						get_logger('container_'+id).info(exc)			
							
					# export_container_logs(id, v_count)	

					# if sw_found_pwa(id,v_count) and CRAWL_SW==True:						
					# 	print('sw found', id)
					# 	with open('./data/crawl_sites_sw.csv','a+') as f:
					# 		f.write(id+','+url+',0\n')
					# 	rank = id.split('_')[-1] 
					# 	dbo.update_alexa_sites_table(rank, None, 'is_sw_found', 'True')

					stop_container(id)
					
					processed_url_ids.add(id)	
			except Exception as e:
				##  Stop the containers that didn't complete before timeout and export data
				for future in futures.keys():
					id, v_count, url = futures.pop(future)				
					try:				
						get_logger('container_'+id).info(get_time() + 'Container_'+ str(id) +': Timeout Occured!!'	)	
					except concurrent.futures.TimeoutError as ex:
						get_logger('container_'+id).info(get_time() +  'Container_' + str(id) +': Timeout occured!!')
					except Exception as exc:
						get_logger('container_'+id).info(get_time() +  'Container_' + str(id) +': Exception ')
						get_logger('container_'+id).info(exc)			
							
					export_container_logs(id, v_count)	
					# if sw_found_pwa(id,v_count) and CRAWL_SW==True:
					# 	rank = id.split('_')[-1]
					# 	dbo.update_alexa_sites_table(rank, None, 'is_sw_found', 'True')
					# 	with open('./data/crawl_sites_sw.csv','a+') as f:
					# 		f.write(id+','+url+',0\n')
					# else:
					# 	rank = id.split('_')[-1]
					# 	dbo.update_alexa_sites_table(rank, None, 'is_crawled', 'False')
					stop_container(id)
								
	return processed_url_ids

def stop_running_containers():
	for c in client.containers.list():
		print (c)			
		c.stop()
		c.remove()

def fetch_urls_from_db(count=0):
	if count>0:
		print('Fetching URLS ::'+str(count))
		#results = api_requests.fetch_urls_api(count,'true','true')
		results = dbo.get_seed_urls(CRAWL_SW, count)
		crawl_urls={}
		for item in results:
			
			id = id_prefix + str(item[0])
			url = item[1]			
			crawl_urls[str(id)]={'url': url,'count':0}
			
			if CRAWL_SW:
				dbo.update_alexa_sites_table(item[0], None,'is_crawled','True')
			else:
				dbo.update_alexa_sites_table(item[0], None,'is_analyzed','True')
			
		return crawl_urls
	return {}


def fetch_urls_with_notifications(count=100):

	crawl_urls={}
	print('Fetching URLS ::')
	# results = api_requests.fetch_urls_api(count,'true','true')

	# sites = ['https://my.sweeps4life.com/?aff_sub=23&aff_id=1039&aff_sub5=swrota&aff_sub4=0&aff_sub2=15041&first_name=&last_name=&email=&street1=%7Baddress%7D&city=Athens&state_initials=%7Bstate%7D&zipcode=&gender=%7Bgender%7D&date_of_birth=%7Bdob%7D&phone=%7Bphone%7D',
	# 'https://get.topsweeps.com/?transaction_id=102209154234281659105440911501&aff_id=1102&offer_id=557&url_id={url_id}&firstname={firstname}&lastname={lastname}&email=&dob-m={dob-m}&dob-d={dob-d}&dob-y={dob-y}&gender={gender}&address={address}&phone={phone}&city={city2}&state={state}&zip={zip}&aff_sub=PN_TAG_01ARATOP_s&aff_sub2=2019-08-25T16:55:48.150Z&aff_sub3=&aff_sub4=&aff_sub5=push&i={i}',
	# 'https://win.click4riches.info/api/offer',
	# 'https://win.omgsweeps.info/api/offer',
	# 'https://u-s-news.com/todays-top-stories/'	
	# ]

	# for i,url in enumerate(sites):
	# 	crawl_urls['M_run2_'+str(i)] = {'url':url, 'count':0}


	if '.csv' in urls_path:
		import csv 
		with open(urls_path) as cf:
			csvreader = csv.DictReader(cf, delimiter=',')
			i = 0
			for row in csvreader:
				# print(row)
				i +=1
				# if  not row['id'].isdigit():
				# 	continue 
				
				id = id_prefix + str(row['id'])
				url = row['url']
				if int(row['id'].split('_')[2]) <4000:
					if (os.path.exists('./sw_sec_containers_data/container_'+id)):
						continue
					crawl_urls[id] = {'url':url, 'count':0}
				
	elif '.json' in urls_path:
		with open(urls_path,'r') as o:
			sites = json.loads(o.read())			
		for item in sites:
			id = id_prefix+(item['Country']['Rank'])
			url = 'https://' + item['DataUrl']	
			if not os.path.exists('./output_logs/container_'+id+'.log'):
				crawl_urls[str(id)]={'url': url,'count':0}


	#
	return crawl_urls
	

def process_urls_with_notifications():	
	while True:
		notification_urls  =  fetch_urls_from_db(max_containers) #fetch_urls_with_notifications()
		notification_urls_keys = sorted(notification_urls.keys(), key = lambda x: int(x.split('_')[-1]))

		print('started processing')
		print(len(notification_urls))	
		print(notification_urls_keys[:5])
		for i in range(0,len(notification_urls),max_containers):	

			notification_urls_set = {k:notification_urls[k] for k in notification_urls_keys[i:i+max_containers]}
			while notification_urls_set:			
				processed_ids = process_urls_parallel(notification_urls_set, collection_script, container_timeout, max_containers)		
				## Retain only those containers that requested notifications
				notification_urls_set = {id:info for id,info in notification_urls_set.items() if info['count']>0 or id in processed_ids}
				for key in notification_urls_set.keys():
					itm = notification_urls_set[key]							
					if itm['count'] == iteration_count:
						## Resume each container `iteration_count` number of times
						notification_urls_set.pop(key)
						notification_urls.pop(key)
					else:
						itm['count'] = itm['count']+1
				if len(client.containers.list())>30:
					print('docker pruning started!!')
					docker_prune()

		
def main():
	stop_running_containers()
	'''
	prune unused removed containers
	'''
	docker_prune()
	set_config()
	print('SWSec_PWA :: Collecting SW Logs...' )
	process_urls_with_notifications()



if __name__ == "__main__":
    main()
