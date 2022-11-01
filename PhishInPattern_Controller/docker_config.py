import os

project_dir = os.getcwd()

#Docker
docker_image = 'phishmesh_puppeteer:ver2'
docker_user = 'pptruser'
docker_container_home = '/home/pptruser/'
vols ={ 
		project_dir + '/config' :{'bind':docker_container_home + 'app/PhishMeshCrawler/config','mode':'ro'}
		# project_dir + '/demo' : { 'bind': docker_container_home + 'app/PhishMeshCrawler/', 'mode': 'rw' }
	  }
''', 
	docker_shared_dir_root + '/logs'          :{'bind':docker_container_home + 'logs','mode':'rw'},
	        docker_shared_dir_root + '/screenshots'   :{'bind':docker_container_home + 'screenshots','mode':'rw'},
            docker_shared_dir_root + '/resources'     :{'bind':docker_container_home + 'resources','mode':'rw'},
	       
	      }
'''
collection_script   = 'crawl_page.py'


ANALYSIS_MAX_CONTAINERS = 10
ANALYSIS_TIMEOUT = 1200  # 900 ->15 mins


CONFIG_EXPORT_PATH = './containers_data/'

CRAWL_URL_PATH = '../SWSec_Data/high_deny_score_sites.csv' #'../SWSec_Data/navigatorserviceworkerregister.csv'
ANALYSIS_URL_PATH = '../data/phish.csv'

###
# To be changed as needed
###
CRAWL_SW = False
IS_MALICIOUS = False

if CRAWL_SW ==True:
	CONFIG_EXPORT_PATH = './crawl_quiet_permissions_data/' './crawl_containers_data/'
else:
	CONFIG_EXPORT_PATH = './phish_containers_data/'

def get_logger(name, init=0):    
	import logging

	format='%(name)s - %(funcName)20s() - %(message)s'

	logger = logging.getLogger(name = name)
	# print(name,init,logger)
	if init == 0:
		return logger
	else:
		handler = logging.FileHandler('./output_logs/'+name+'.log')
		handler.setFormatter(logging.Formatter(format))
		logger.setLevel(logging.INFO)
		logger.addHandler(handler)
		return logger
