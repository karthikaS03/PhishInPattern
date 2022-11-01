
import sys
import time
from datetime import datetime

from gglsbl import SafeBrowsingList
sys.path.append('/home/sk-lab/Desktop/PhishProDetector/PhishMeshCrawler/')
from  config import phish_db_config
from database import phish_db_layer


def run_sync(sbl):
    try:
        sbl.update_hash_prefix_cache()
    except (KeyboardInterrupt, SystemExit):
        print ("Exiting")
        sys.exit(0)
    except Exception as e:
        print ("Error in syncing", e)
        time.sleep(3)


def main():
    sbl = SafeBrowsingList(phish_db_config.gsb_key, db_path=phish_db_config.gsb_db_path)
    run_sync(sbl)  
    while True:
        links = phish_db_layer.fetch_gsb_urls()
        query_time = datetime.now()
        print ("GSB Update time:", str(query_time))
        
        print ("Got updated GSB list. Now looking up %s domains: %s" % (
                    len(links), str(datetime.now())))
        for l in links:
            # print(l)
            try:
                result = sbl.lookup_url(l.open_phish_url)
                print(result)
                result = "%s" % (result,)
                phish_db_layer.update_gsb_table(l.open_phish_url, result)
            except Exception as e:
                print ("Exception. Skipping this domain: ", l.open_phish_url, e)
        run_sync(sbl)
        print ("Done inserting into DB. Will update GSB list again", str(datetime.now()))
        time.sleep(3600)

if __name__ == '__main__':
    main()
