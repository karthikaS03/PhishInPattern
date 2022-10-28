 
import pandas as pd 
import concurrent.futures
import docker
import time
import datetime
import os
import json 
import sys
import csv 
sys.path.append('/home/sk-lab/Desktop/PhishProDetector/PhishMeshCrawler/')
from database import phish_db_layer, phish_db_schema
from docker_config import *
from docker_monitor import *
from datetime import timedelta

client = docker.from_env()

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
		id_prefix = 'Phish_'
		iteration_count = 0
		
	else:
		container_timeout = ANALYSIS_TIMEOUT
		urls_path = ANALYSIS_URL_PATH
		max_containers = ANALYSIS_MAX_CONTAINERS
		id_prefix = 'Mal_' if IS_MALICIOUS else 'Phish_'
		iteration_count = 0
		

def process_urls_parallel(analysis_urls, script_file, cont_timeout, max_cont):
	futures={}
	processed_url_ids = set()
	urls = analysis_urls.copy()
	with concurrent.futures.ProcessPoolExecutor(max_workers = max_cont) as executor:
		while len(urls)>0:
			## Submit jobs to container ##
			for i in range(min(len(urls),max_cont)):
				id = list(urls.keys())[0]
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
							
					
					stop_container(id)
					
					processed_url_ids.add(id)	
			except Exception as e:
				##  Stop the containers that didn't complete before timeout and export data
				fts = list(futures.keys())
				for future in fts:
					id, v_count, url = futures.pop(future)				
					try:				
						get_logger('container_'+id).info(get_time() + 'Container_'+ str(id) +': Timeout Occured!!'	)	
					except concurrent.futures.TimeoutError as ex:
						get_logger('container_'+id).info(get_time() +  'Container_' + str(id) +': Timeout occured!!')
					except Exception as exc:
						get_logger('container_'+id).info(get_time() +  'Container_' + str(id) +': Exception ')
						get_logger('container_'+id).info(exc)			
							
					export_container_logs(id, v_count)	
					
					stop_container(id)
								
	return processed_url_ids

def stop_running_containers():
	for c in client.containers.list():
		if 'Phish' in c.name:
			print (c.name)			
			c.stop()
			c.remove()

def fetch_urls_from_db(count=0):
	if count>0:
		phishtank_dets = phish_db_layer.fetch_openphish_urls(count) #phish_db_layer.fetch_phishtank_urls(count)
		print('Fetching URLS ::'+str(count))
		
		crawl_urls={}
		for item in phishtank_dets:
			# print(isinstance(item , phish_db_schema.Open_Phish_Links))
			id = id_prefix + (str(item.phish_tank_ref_id) if not isinstance(item , phish_db_schema.Open_Phish_Links)  else 'openphish_'+ str(item.open_phish_link_id))
			crawl_urls[str(id)] = {'url' : item.phish_tank_url if not isinstance(item , phish_db_schema.Open_Phish_Links) else item.open_phish_url, 'count':0}			
			item.is_analyzed = True
			phish_db_layer.update_analysis_url(item)
		return crawl_urls
	return {}


def fetch_from_file():
	urls_path =  '../data/phishing_dumps/csv/tmp_examples_phishing_{}.csv'.format((datetime.datetime.today()-timedelta(1)).strftime('%d%m%Y'))
	# urls_path = '../data/phishing_dumps/csv/tmp_examples_phishing.csv'phishing_seen_recently_

	# crawl_urls = {'test123': {'url':'https://www.google.com/recaptcha/api2/demo', 'count':0}}
	crawl_urls = {}
	if '.csv' in urls_path:		
		with open(urls_path) as cf:
			csvreader = csv.DictReader(cf, delimiter=',')
			i = 1
			for row in csvreader:
				# print(row)
				# if i>5:
				# 	break
				if 'openphish' in urls_path:
					i += 1
					print(row['url'])
					# t_date = urls_path.split('/')[-1].replace('.csv','')
					id = id_prefix +  'openphish' +'_'+ str(i)
					url = row['url']				
					crawl_urls[id] = {'url':url, 'count':0}

				elif 'rank' not in row:
					# if i<737:
					# 	i +=1
					# 	continue
					i += 1
					t_date = urls_path.split('/')[-1].replace('.csv','')
					id = id_prefix +  'palo_' + str(t_date)+'_'+ str(i)
					url = row['url']
					url = url if url.find('http')==0 else 'http://'+url				
					crawl_urls[id] = {'url':url, 'count':0}

				elif  int(row['rank'])>0:
					i +=1		
					id = id_prefix + 'top_'+row['rank']+'_'+ str(i)
					url = row['url']				
					crawl_urls[id] = {'url':url, 'count':0}
								
	return crawl_urls

def process_phishing_urls():	
	while True:
		phish_urls  =   fetch_from_file() #fetch_urls_from_db(max_containers) #fetch_from_file() #
		print(len(phish_urls))
		processed_ids = process_urls_parallel(phish_urls, collection_script, container_timeout, max_containers)		
		if len(client.containers.list())>30:
			print('docker pruning started!!')
			docker_prune()
		break

		
def main():
	# stop_running_containers()
	'''
	prune unused removed containers
	'''
	docker_prune()
	set_config()
	print('PhishMeshController :: Started Crawling Phish URLs...' )
	process_phishing_urls()



if __name__ == "__main__":
    main()
