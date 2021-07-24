
from database import phish_db_schema
from database import phish_db_layer
import crawl_page
import asyncio
import multiprocessing
import time

phishtank_dets = phish_db_layer.fetch_phishtank_urls()

# phishtank_dets = phishtank_dets

# print(phishtank_dets)

def initiate_crawl(phish_url,phish_id):
	asyncio.get_event_loop().run_until_complete( crawl_page.crawl_web_page(phish_url, phish_id))


for item in phishtank_dets:
	print(item)
	# asyncio.get_event_loop().run_until_complete( crawl_page.crawl_web_page(item['phish_url'], item['phish_id']))
	p = multiprocessing.Process(target=initiate_crawl, args=(item.phish_tank_url, item.phish_tank_ref_id))
	item.is_analyzed = False
	phish_db_layer.update_analysis_url(item)
	p.start()

	# Wait for 10 seconds or until process finishes
	# p.join(300)
	# wait incrementally for upto 5 mins
	for t in range(60,300,60):
		p.join(60)
		# If thre0ad is still active
		if not p.is_alive():
			item.is_analyzed = True
			phish_db_layer.update_analysis_url(item)
			break
	if p.is_alive():
		# print "running... let's kill it..."
		p.terminate()
		time.sleep(5)
		print(p)
		print('is_process_alive',p.is_alive())
		item.is_analyzed = True
		phish_db_layer.update_analysis_url(item)
		# if p.is_alive():		
		# 	p.kill()
		# 	p.join()

