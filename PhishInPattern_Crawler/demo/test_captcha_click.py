import sys
# sys.setdefaultencoding('utf-8')
import os
import asyncio
from pyppeteer import launch
import time
import argparse
import pyautogui

dir_path = os.path.abspath(os.path.dirname(__file__))
dir_path = dir_path +'/../../data'

async def crawl_web_page(phish_url,site_obj, phish_id=-1):

    browser = await launch({ 'headless':False, 
                                'ignoreHTTPSErrors':True, 
                                'args': [                             
                                '--no-sandbox',
                                '--disable-setuid-sandbox',                               
                                '--start-maximized',
                                '--ignore-certificate-errors',
                                '--ignore-certificate-errors-spki-list'
                                ]
                            })
        

    pup_page = await browser.newPage()

    ### Visit the page 
    try:
        time.sleep(3)
        await pup_page.setViewport({'width':1366, 'height':768})
        await pup_page.goto(phish_url, {'waitUntil':['networkidle0', 'domcontentloaded'],'timeout':900000 })		
    except Exception as e:
        print(e)
    
    time.sleep(5)

    ### move randomly
    pyautogui.moveTo(100,200)
    pyautogui.dragTo(109,437)
    time.sleep(2)
    ## click nocaptcha
    pyautogui.click(109,437)



async def main(url, phish_id, time_out=600):

	try:
		site_obj = None
		# Starts the crawling process with a execution timeout
		await asyncio.wait_for( crawl_web_page(url, site_obj, phish_id), timeout = time_out)
	except asyncio.TimeoutError:
		print('timeout')


parser = argparse.ArgumentParser(description="Crawl phishing links")
parser.add_argument('url', default="https://recaptcha-demo.appspot.com/recaptcha-v2-checkbox.php" ,type=str, help= "URL to crawl")
parser.add_argument('--phish_id', default=-1, help="Unique id from phishtank database(optional)" )
parser.add_argument('--timeout', default=600, help="Time duration after which the program will terminate" )

if __name__ == '__main__':
	args = parser.parse_args()
	print(args.url, args.phish_id, args.timeout)
	asyncio.get_event_loop().run_until_complete(main(args.url, args.phish_id, args.timeout))