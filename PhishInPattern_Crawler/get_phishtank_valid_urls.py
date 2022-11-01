from datetime import datetime
import requests
import json
from database import phish_db_schema
from database import phish_db_layer
from dateutil import parser
import tldextract
import time


def is_url_online(url):
	try:
		r = requests.get(url,verify=False,stream=True)
		if r.status_code == 200:              
			return 'Online'
		return 'Offline'
	except Exception as e:		
		return 'Notreachable'


def get_phishtank_urls():
	api_url = 'http://data.phishtank.com/data/72a9d2517a46cddac6356702810df747613f492bac9a7877c37b518989811ee8/online-valid.json'
	r = requests.get(api_url)
	if r.status_code ==200:
		phishtank_urls = r.json()
		with open('phishtank_online_urls.json', 'w') as f:
			json.dump(phishtank_urls,f, indent=4)
	time.sleep(5)
	record_phishtank_url_details()

def record_phishtank_url_details():
	
	sites = []
	with open('./phishtank_online_urls.json','r') as f:
			sites = json.load(f)
	for site in sites:	
		try:		
			# phishtank_urls[int(e['phish_id'])] = e
			status = is_url_online(site['url'])
			domain = '.'.join(tldextract.extract(site['url'])[1:])
			link = phish_db_schema.Phish_Tank_Links( phish_tank_ref_id = site['phish_id'] , phish_tank_url = site['url'] , 
				recorded_datetime = parser.parse(site['submission_time']).date()  , 
				verification_datetime = parser.parse(site['verification_time']).date(), status = status )
			phish_db_layer.add_phish_tank_link(link)
			domain = phish_db_schema.Domains(domain_name= domain, trust_score= 0)
			domain.domain_id = phish_db_layer.add_domain_info(domain)
			site_2 = phish_db_schema.Sites(site_url = site['url'], phish_tank_ref_id = site['phish_id'],  domain_id = domain.domain_id)
			phish_db_layer.add_site_info(site_2)	
			# break;
		except:
			continue

def get_openphish_urls():
	api_url = 'https://openphish.com/feed.txt'
	r = requests.get(api_url)
	links = r.text
	with open('../data/openphish_links.csv', 'w') as f:
		f.write('url\n'+links)
	with open('../data/open_phish_feeds/openphish_links_'+str(datetime.datetime().now())+'.csv', 'w') as f:
		f.write('url\n'+links)
	time.sleep(5)
	record_openphish_url_details()

def record_openphish_url_details():
	import csv

	with open('../data/openphish_links.csv','r') as cf:			
		csvreader = csv.DictReader(cf, delimiter=',')
		i = 1502
		for row in csvreader:		
			try:						
				status = is_url_online(row['url'])
				domain = '.'.join(tldextract.extract(row['url'])[1:])
				link = phish_db_schema.Open_Phish_Links( open_phish_url= row['url'] , status = status )
				phish_db_layer.add_open_phish_link(link)				
			except:
				continue

while True:

	get_phishtank_urls()
	for i in range(0,5,3600):		
		get_openphish_urls()
		time.sleep(5)
	time.sleep(3600)