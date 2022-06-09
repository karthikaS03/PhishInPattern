
from re import sub
import sys
# sys.setdefaultencoding('utf-8')
import os
import hashlib
import screenshot_slicing
import asyncio
from pyppeteer import launch
from phish_logger import Phish_Logger
from database import phish_db_schema
from database import phish_db_layer
from datetime import datetime
import page_element
import time
import MNB_field_classifier
import tldextract
import argparse
import extra_scripts
import json
import requests
import base64
import pyautogui

dir_path = os.path.abspath(os.path.dirname(__file__))
dir_path = dir_path +'/../../data'

logger = Phish_Logger.get_phish_logger('phish_logger', "crawl_page.py")
event_logger = Phish_Logger.get_phish_logger('phish_events')

textTags=['DIV','SPAN','TD','LABEL','H1','H2','H3','P','STRONG']
OFFSET_X, OFFSET_Y = 20, 130

password = None

#### MAIN ####
def add_InnerText(element):	
	# print('check: addInnerText')
	password = None
	text=filterData(element.parsed_texts.pop())
	score=-1
	if 'username' in text.lower():
		category ="username"
		value = MNB_field_classifier.get_category_input_value(category)
		category="Name"
	else:
		category, score  = MNB_field_classifier.classify(text)
		value = MNB_field_classifier.get_category_input_value(category)
	if password != None and category == 'Password':
		value=password
	elif password == None and category == 'Password':
		password=value
	element.parsed_texts.append(text)
	element.values.append(value)
	element.categories.append(category)
	element.scores.append(score)
	
	return element

def filterData(text):
	try:
		#print('Text to filter:', text)
		# text = text.decode('unicode_escape').encode('ascii','ignore').encode('utf-8').rstrip().lstrip()
		# text = text.encode('ascii','ignore').decode().rstrip().lstrip()
		if text.find("\n")>=0:    
			text = text[:text.index("\n")]
	except Exception as e:
		print(e)
	return text

def parse_elements(res,path,page):
	# try:
	fields=[]
	elementCount=0
	#Enumerate all the elements in the page
	for index,r in enumerate(res):
		#Filter Input and Select tags which are not hidden
		# print(r)
		try:
			if any(tag in r["tag"] for tag in ['INPUT']) and 'type' in r and r["type"] not in ['hidden','button','submit','reset','radio','checkbox'] and r["visibility"]!='hidden':
				
				flag=False
				elementCount=elementCount+1
				elementId   = r["id"] if r["id"]!=None else "Unknown"+str(index)
				elementName = r["name"] if r["name"]!=None else "Unknown"+str(index)
				element = page_element.Page_Element(elementName,r["tag"],elementId)
				element.form = r["form"]
				element.frameIndex = r['frameIndex']
				element.position = ";".join(map(str,[r["left"],r["top"],r["right"],r["bottom"]]))
				element.parsed_texts.append(elementName)
				element.parsed_methods.append("Element Name")
				element = add_InnerText(element)  
				flag=True if len(element.categories[-1])>1 else False
				element.parsed_texts.append(elementId)
				element.parsed_methods.append("Element Id")
				element = add_InnerText(element)
				flag=True if len(element.categories[-1])>1 else False                

				# print( "Element" + r["name"])
				for ind,itm in enumerate(reversed(res[:index])):
					if abs(itm["left"]-r["left"])<15 and abs(itm["top"]-r["top"])<5 and any(tag in itm["tag"] for tag in textTags):
						if itm["innerText"] !=None:	  
							text = filterData(itm["innerText"])
							#print "Left" + itm["innerText"]
							if len(text)>1 and len(text)<35 :							
								element.parsed_texts.append(text)
								element.parsed_methods.append("LeftSide_InnerText")
								element = add_InnerText(element)                
								flag=True if len(element.categories[-1])>1 else False
								break       
					elif abs(itm["top"] - r["top"])<15 and abs(itm["left"]-r["left"])<5 and any(tag in itm["tag"] for tag in textTags):
						if itm["innerText"] !=None:	  		
							text = filterData(itm["innerText"])				
							#print "top" +itm["innerText"]
							if len(text)>1 and len(text)<35 :							
								element.parsed_texts.append(text)
								element.parsed_methods.append("TopSide_InnerText")
								element = add_InnerText(element)           
								flag=True if len(element.categories[-1])>1 else False
								break
				if flag==False:           
					text=screenshot_slicing.img_to_text(path,'I',r["left"]-5,r["top"]-5,r["right"]+5,r["bottom"]+5,3) 
					
					text = filterData(text)
					
					if len(text)>1 :    					
						element.parsed_texts.append(text)
						element.parsed_methods.append("Image_OCR_Read_Inside")
						element = add_InnerText(element)  					    
						flag=True if len(element.categories[-1])>1 else False       
				# print('check : 2')
				if flag==False:           
					text=screenshot_slicing.img_to_text(path,'L',r["left"]-200,r["top"],r["left"],r["bottom"],3)
					
					text = filterData(text)  
					if len(text)>1 :      					
						element.parsed_texts.append(text)
						element.parsed_methods.append("Image_OCR_Read_Left")
						element = add_InnerText(element)                    	
						flag=True if len(element.categories[-1])>1 else False  
					else:          
						text=screenshot_slicing.img_to_text(path,'T',r["left"],r["top"]-(r["height"]+5),r["right"],r["bottom"]-(r["bottom"]-r["top"]),3)  
						
						text = filterData(text)    
						if len(text)>1 :						
							element.parsed_texts.append(text)
							element.parsed_methods.append("Image_OCR_Read_Top")
							element = add_InnerText(element)                
							flag=True if len(element.categories[-1])>1 else False        
				# print('check:3')
				if r["placeholder"]!='null' and flag!=True:      
					flag=True
					element.parsed_texts.append(r["placeholder"])
					element.parsed_methods.append("placeholder")
					element = add_InnerText(element)
				# print('check:4')
				category, value, parsed_text, parsed_method = element.get_category_value()
				logger.info('parse_elements(%s) Element ->  Name: %s ;  Html_Id: %s ; Category: %s ; Value: %s; Parsed_text: %s; Parsed_method:%s' % ( page.page_image_id,element.name, element.html_id,category,value,parsed_text,parsed_method))
				category_id = phish_db_layer.find_category_id(category)
				# print('check:5')
				element_db = phish_db_schema.Elements(element_name = element.name, 
													element_tag = element.tag, 
													element_html_id = element.html_id, 
													element_position =element.position, 
													element_form = element.form, 
													element_value = value,
													element_frame_index = element.frameIndex,
													field_category_id = category_id,
													element_parsed_text = parsed_text, 
													element_parsed_method = parsed_method)
				page.elements.append(element_db)
				
				print('parse_elements(%s) Element ->  Name: %s ;  Html_Id: %s ; Category: %s ; Value: %s; Parsed_text: %s; Parsed_method:%s' % ( page.page_image_id,element.name, element.html_id,category,value,parsed_text,parsed_method))
		except Exception as pre:
			print('Parse_Elements :: Exception !! ',pre, r)	
	event_logger.info('parse_elements(%s, %s):: Elements Count :: %s'%(page.page_url,page.page_image_id, len(page.elements)))
	return page

def get_frame(frameIndex, pup_page):
	frame = pup_page
	
	if frameIndex != -1 and pup_page.frames!=None:
		frame = pup_page.frames[frameIndex+1]
	
	return frame

async def reset_element(element, page, field_selector):
	try:
		# await get_frame(element.element_frame_index, page).click()
		if  await element.getProperty("type") not in ["hidden","button","reset","a","checkbox","submit","radio"] and await element.isIntersectingViewport(): 
				
			await element.focus()
			# await  get_frame(element.element_frame_index, page).focus(field_selector)			
			cnt = 0
			# await page.keyboard.down('Control')
			# await page.keyboard.press('A')
			# await page.keyboard.up('Control')
			# await page.keyboard.press('Backspace')
			# await page.keyboard.press('Enter')
			while cnt <= 50:
				await element.press('Backspace')
				cnt = cnt+1
			while cnt <= 50:
				await element.press('Delete')
				cnt = cnt+1
			
	except Exception as e:
		
		logger.info('reset_element(): Exception!!') 

async def crawl_web_page(phish_url, site_obj, site_pages, phish_id=-1):

	browser = await launch({ 'headless':False, 
							 'ignoreHTTPSErrors':True, 
							 'args': [                             
	                            '--no-sandbox',
	                            '--disable-setuid-sandbox',                               
	                            '--start-maximized',
	                            '--ignore-certificate-errors',
								'--ignore-certificate-errors-spki-list',
								'--allow-running-insecure-content',
								'--disable-features=IsolateOrigins',
								'--disable-web-security',
								 '--window-size=1366,768'
	                           ]
	                     })
	 

	pup_page = await browser.newPage()

	temp = None 
	samePage = 0
	count=phish_id
	page_count = 0
	res_page_count = 0
	page_requests = []
	page_responses = []

	async def is_navigate_success():
		try:
			# await asyncio.sleep(10)
			# res = None
			try:
				await pup_page.waitForNavigation({'waituntil':'networkidle2','timeout':15000})
			except Exception as ex:
				print('navigation timeout!!!')

			await pup_page.addScriptTag({'content':extra_scripts.js_dom_scripts})
			dom_tree= await pup_page.evaluate("()=>get_dom_tree()") 			
			print('is_navigate_success ::' , temp!=dom_tree)
			# print(dom_tree)
			## Check if the page is naviagted to a page with different content
			return  temp != dom_tree 
		except Exception as e:
			print('is_navigate_success :: Exception ',e)

	async def clear_overlays():

		field_buttons = await pup_page.JJ('button')

		### Click any popup buttons
		# for field_btn in field_buttons:
			
		# 	if await field_btn.isIntersectingViewport():
		# 		try:				
		# 			await field_btn.click()   
		# 		except Exception as fe:
		# 			print(fe)

		print('overlay cleared')
		## Generate random clicks to dispose alerts and popup boxes
		#species: [gremlins.species.clicker({clickTypes:['click', 'dblclick']})],strategies: [gremlins.strategies.bySpecies({delay: 500, nb: 50 })]
									
		await pup_page.evaluate("""() => { gremlins.createHorde({
								species: [gremlins.species.clicker({clickTypes:['click', 'dblclick']})],
								strategies: [gremlins.strategies.bySpecies({delay: 200, nb: 20 })],
								mogwais: [gremlins.mogwais.alert()]								
							}).unleash() }"""
							)
		await asyncio.sleep(10)

	async def get_noninput_elements(screenshot_path): 

		###
		### javascript code to calculate size of all elements in the page and sort them in decreasing manner
		### Returns poisiton of the element with the size and tag 
		###

		all_elements = []

		for i,f in enumerate(pup_page.frames):
			await f.addScriptTag({'content':extra_scripts.js_dom_scripts})
			frame_elements = await f.evaluate("()=> process_elements(document.body)")
			
			for fe in frame_elements:
				fe['frame_no'] = i
				all_elements.append(fe)            
			
		all_elements.sort(key = lambda x: x['size'], reverse = True)

		ignore_tags = ['INPUT', 'A', 'SCRIPT', 'LI', 'UL', 'FORM']
		for i,el in enumerate(all_elements):
			dim = list(map(float,el['dimension'].split(';'))) if len(el['dimension'])>0 else None
			
			### check if total size is greater thean a threshold and the height is less than threshold
			if el['tag'] not in ignore_tags and el['size']>5000 and dim!=None and dim[4]<150 and  el['class']=='survey_button':			
				txt = screenshot_slicing.img_to_text(screenshot_path, 'captcha_'+str(el['pos'])+'_'+str(el['size'])+'_'+el['tag'], dim[0], dim[2], dim[1], dim[3] , 3)
				
	async def get_event_listeners_old() :
		try:
			session = await pup_page.target.createCDPSession()

			# Evaluate query selector in the browser
			res = await session.send('Runtime.evaluate', {
			"expression" : "document.querySelectorAll('*')"
			})
			# print( res)
			# Using the returned remote object ID, actually get the list of descriptors
			result = await session.send('Runtime.getProperties', {'objectId' : res['result']['objectId']}) ; 
			
			# print(result['result'])
			# Filter out functions and anything that isn't a node
			descriptors= list(filter(lambda x:  x.get('value', None) != None and x['value'].get('objectId', None) !=None and x['value'].get('className',None) != 'Function' , result['result']))
			# print(descriptors)

			elements = []

			for descriptor  in descriptors:
				objectId = descriptor['value']['objectId']

				## Add the event listeners, and description of the node (for attributes)
				all_listeners = await session.send('DOMDebugger.getEventListeners', {'objectId' : objectId })
				node_desc = await session.send('DOM.describeNode', { 'objectId' : objectId })
				if len(all_listeners['listeners']) > 0:
					elements.append({'node' : node_desc['node'], 'listeners': all_listeners['listeners'] })
				# print(node_desc, all_listeners)

				# elements.append(descriptor)
			with open(dir_path+'/'+str(count)+'_'+str(page_count)+'_listeners_old.log', 'w') as lf:
				json.dump(elements, lf, indent=2) 

			return elements
		except Exception as ee:
			print('Exception in get_listeners_old ', ee)
			return []

	async def detect_known_captcha(page_image_det ):

		try:
			### add all JS scripts to detect the presence sof captchas
			await pup_page.addScriptTag({'content':extra_scripts.js_captchas})

			captcha_methods = [" findRecaptchaClients()", " find_recaptcha()", " find_hcaptcha()", " find_keycaptcha()"]
			for cm in captcha_methods:
				captcha_details = await pup_page.evaluate("""()=>"""+cm)
				if captcha_details:
					cap_info = phish_db_schema.Captcha_Info( page_image_id = page_image_det, 
															captcha_details = str(captcha_details)
															)
					event_logger.info('crawl_page_info(%s,%s) :: Known Captcha Found ::{"captcha_method":%s, "page_count" : %s, "curr_url": %s , "page_image_id" : %s}'%(str(count), phish_url, cm,loop_count, pup_page.url, page_image_det))
					phish_db_layer.add_captcha_info(cap_info)
		except:
			pass

	async def handle_request(req):
		###
		### Intercept Page Requests and log them
		###
		req.__setattr__('_allowInterception',True)
		def log_request_details(rq):
			
			try:
				req_url = rq.url
				event_logger.info("handle_request :: {'method':%s, 'url':%s, 'post_data': %s,'headers': %s} "%(rq.method, req_url, rq.postData,rq.headers))
				req_domain =  '.'.join(tldextract.extract(req_url)[1:]) 
				req_info = phish_db_schema.Page_Request_Info(request_url = req_url[:10000], 
															request_domain = req_domain, 
															request_method = rq.method, 
															request_type = rq.resourceType
															,req_id = rq._requestId,
															post_data = rq.postData[:1990] if rq.postData !=None else rq.postData,
															headers = str(rq.headers)[:10000] if rq.headers !=None else rq.headers
															)

				page_requests.append(req_info)
			except:
				pass
		if not ('gremlin' in req.url):
			log_request_details(req)

			### log details of requests involved in the redirections
			for r in req.redirectChain:			
				log_request_details(r)

		await req.continue_()

	async def handle_response(res ):
		###
		### Fetch Responses, Store them and their hash in database 
		###
		if not 'gremlin' in res.url:
			res_name = (res.url.split('?')[0]).split('/')[-1]
			res_name = res_name if len(res_name)>1 else 'res_' + str(site_obj.site_id) + '_' + res.request._requestId
			# res_count = res_count + 1
			dpath = dir_path + '/resources/' + str(count)		
			digest = ''

			if not os.path.exists(dpath):
				os.makedirs(dpath)
			
			file_path = "{}/{}_{}".format(dpath , str(res_page_count), res_name )
			try:
			
				# Get response content and store it in a file
				txt = await res.buffer()			
				txt_type = 'w' if type(txt) is str else 'wb' 
				with open(file_path, txt_type ) as fw:	
					fw.write(txt)
			
				# Generate hash of requested file
				hasher = hashlib.sha1()
				with open(file_path, 'rb') as afile:
					buf = afile.read()    
					hasher.update(buf)
				digest = hasher.hexdigest()			
			except Exception as e:
				pass
				# logger.info('handle_response: Exception!! ::'+res.url+' :: '+str(e))
			event_logger.info('handle_response :: %s '%(res.url))
			rsp_info = phish_db_schema.Page_Response_Info(	response_url = res.url[:10000], 
															response_file_path = file_path, 
															response_file_hash = digest,
															response_status = str(res.status),
															response_headers = str(res.headers)[:10000] if res.headers !=None else res.headers
														)
			# phish_db_layer.add_page_rsp_info(rsp_info)
			page_responses.append(rsp_info)

	async def is_field_visible(el):
		l,t,r,b = map(float,el.element_position.split(';'))
		if (r-l>0 and b-t >0):
			return True
		return False

	async def get_field(field_selector, frameIndex):
		###
		### Ger field details based on the selector
		###

		form = ''
		form_id=''
		try:
			frame = get_frame(frameIndex, pup_page)
			try:
				await frame.waitFor(field_selector)
			except:
				pass
			field = await frame.J(field_selector)
			try:
				form = await frame.Jeval(field_selector, "(el)=>{ return el.form.name }")
				form_id = await frame.Jeval(field_selector, "(el)=>{ return el.form.id }")
			except:
				return field,form,form_id
			return field, form, form_id
		except Exception as e:
			logger.info('get_field(%s,%s): Exception -> Failed getting field!! %s ;' %(str(field_selector), str(frameIndex), str(e)))
			return None, '', ''
							
	async def input_values(curr_page, curr_url, captcha_result):
		###
		### Iterate through each element and provide respective input
		###

		form = None 
		form_id = None
		field_selector = ''
		if curr_page == None or curr_page.elements== None:
			return form,form_id

		try:
			for element in curr_page.elements:
				try:
					# print(element, is_field_visible(element))
					fv = await is_field_visible(element)
					if not fv:
						continue
					event_logger.info('crawl_page_info(%s,%s): Providing input for Element (%s,%s,%s,%s) ' %(str(count),curr_url,element.element_name,element.element_html_id,element.element_tag,element.element_value))
					field = None		
					field_selector = ''				
					print('Element :: ', element)	

					if element.element_name!=None and len(element.element_name)>0 and 'Unknown' not in element.element_name  :						
						field_selector = 'input[name='+element.element_name+']'					
						field, form, form_id = await get_field(field_selector, element.element_frame_index)

					elif  element.element_html_id != None and len(element.element_html_id)>0 and 'Unknown' not in element.element_html_id :					
						field_selector = 'input[id='+element.element_html_id+']'	
						field, form, form_id = await get_field(field_selector, element.element_frame_index)

					### Type the value in the field 
					if field !=None and await field.isIntersectingViewport(): 
						await reset_element(field, pup_page, field_selector)							
						print('typing value ::', element.element_value)										
						await field.focus()
						await field.type(element.element_value)
						time.sleep(3)
						await get_frame(element.element_frame_index, pup_page).Jeval(field_selector, "(el)=>{ el.blur(); }")
						time.sleep(3)

				except Exception as ve:					
					logger.info('Input Value (%s,%s): Exception -> Failed on entering value ;%s' %(str(count), curr_url, str(ve)))
			try:
				dropdowns = await pup_page.JJ('select')

				for i, dd in enumerate(dropdowns):
					print(dd)
					selected = await dd.JJeval('option', 'v=>v[1].value')
					dd_id = options = await pup_page.JJeval('select','all=> all['+str(i)+'].getAttribute("id")')
					dd_name = options = await pup_page.JJeval('select','all=> all['+str(i)+'].getAttribute("name")')
					print(dd_id,dd_name)
					dd_selector = None
					if dd_id!=None or dd_id!='':
						dd_selector = 'select[id='+dd_id+']'
					elif dd_name!=None or dd_name!='':
						dd_selector = 'select[name='+dd_name+']'
					
					if dd_selector!=None:
						await pup_page.select(dd_selector, selected)
			except Exception:
				pass
			
			await interact_element(captcha_result, 'Captcha')

			### Saving a screenshot of the current page after filling the data			
			path = dir_path+'/images/'+str(count)+"/"+str(count)+'_'+str(page_count)+'_screenshot_processed.png'
			try:
				await pup_page.screenshot({'path':path, 'fullPage': True})
			except Exception as se:
				logger.info('crawl_page_info(%s,%s): Exception -> Failed on saving processed screenshot; %s' %(str(count), curr_url, str(se)))

		except Exception as ee:
			print('Exception in input_elements', ee)
		return form, form_id

	def get_dom_hash(d_tree):
		hasher = hashlib.md5(d_tree.encode())
		return hasher.hexdigest()

	async def get_event_listeners():
		try:
			### to compre if we are missing listeners
			await get_event_listeners_old()

			all_listeners = []
			for i,f in enumerate(pup_page.frames):
				# print('frame processed')                
				await f.addScriptTag({'content':extra_scripts.js_event_scripts})
				frame_listeners = await f.evaluate("()=> listAllEventListeners()")
				all_listeners += frame_listeners
				# print(frame_listeners)

			with open(dir_path+'/'+str(count)+'_'+str(page_count)+'_listeners.log', 'w') as lf:
				json.dump(all_listeners, lf, indent=2) 
		except Exception as e:
			print('get_event_listeners',e)

	async def log_events_helper(log):
		
		if 'KEYLOG' in log.text:
			with open(dir_path+'/'+str(count)+'_'+str(page_count)+'_events.log', 'a') as lf:
					txt = "[CONSOLE LOG][{}] :: {}\n".format(datetime.now().strftime("%m/%d/%Y--%H:%M:%S"), log.text)
					lf.write(txt)
	
	async def interact_element(result,el_keyword):
		try:
			if result['result']!=None and len(result['result']['pred_classes'])>0:
					### keep a log of all captcha detection results
					with open(dir_path+'/'+str(count)+'_'+str(page_count)+'_captchas.log', 'w') as lf:
						json.dump(result, lf, indent=2) 

					### interact with the captchas
					classes = result['result']['class_names']
					for i,pos in enumerate(result['result']['pred_boxes']):
						try:
							if el_keyword in classes[i]:
								print(pos)
								print('***************** '+ el_keyword +' Found ***********************')								
								pyautogui.moveTo(pos[0] + (pos[2]-pos[0])//2 + OFFSET_X , pos[1] + (pos[3]-pos[1])//2 + OFFSET_Y )								
								time.sleep(2)
								## click nocaptcha
								print('clicking on '+el_keyword, (pos[0] + (pos[2]-pos[0])//2 + OFFSET_X , pos[1] + (pos[3]-pos[1])//2 + OFFSET_Y))
								event_logger.info('crawl_page_info(%s,%s): %s Clicked by Position :: (%s, %s, %s, %s) ' %(str(count), curr_url,el_keyword, str(pos[0]), str(pos[1]), str(pos[2]), str(pos[3])))
								pyautogui.click(pos[0] + (pos[2]-pos[0])//2 + OFFSET_X , pos[1] + (pos[3]-pos[1])//2 + OFFSET_Y )
								await asyncio.sleep(2)
								if 'button' in el_keyword:
									is_submit_success =  await is_navigate_success()
									if is_submit_success:
										return True
						except Exception as ce:
							print('Exception in interact_element ::', ce )

					pyautogui.press('esc')
		except Exception as e:
			print('Exception in captcha ::', e )

		return False

	async def detect_captcha_visual(image_path):
		try:
			api_url = "http://172.22.162.44:8905/detect_captcha2"
			file_path = image_path
			im_bytes = None
			with open(file_path,'rb') as f:
				im_bytes = f.read()

			im_64 = base64.b64encode(im_bytes).decode('utf8')
			headers = {'Content-type':'application/json','Accept':'text/plain'}
			payload = json.dumps({"image":im_64,"image_name":image_path.split('/')[-1]})			
			response = requests.post(api_url,data=payload, headers=headers)
			result = response.json()
			return result
		except:
			pass

	async def submit_page(page_det, curr_url, captcha_results):
		
		try:
			is_submit_success = False
			for sub_method in SUBMIT_METHODS:

				print('Submitting method :: ', sub_method)
				event_logger.info('crawl_page_info(%s,%s): Submitting via (%s) ' %(str(count), curr_url, sub_method ))
				form, form_id = await input_values(page_det, curr_url, captcha_results)
				# time.sleep(5)
				print('Entered input values!!')

				try:
					if sub_method == 'visual_button':											
						try:					
							is_submit_success = await interact_element(captcha_results,'button')							
							if is_submit_success:
								break
						except Exception as fe:
							print(fe)
						await asyncio.sleep(5)
						
					if sub_method == 'button':
						field_buttons = await pup_page.JJ('button')
						
						for bt_ind, field_btn in enumerate(field_buttons):
							btn_pos = await field_btn.boundingBox()		
							await field_btn.focus()

							if btn_pos!=None and btn_pos['width']>0 and btn_pos['height']>0 and  await field_btn.isIntersectingViewport():
								try:					
									event_logger.info('crawl_page_info(%s,%s): Button Clicked by Position :: (%s, %s, %s, %s) ' %(str(count), curr_url, str(btn_pos['x']), str(btn_pos['y']), str(btn_pos['width']), str(btn_pos['height'])))
									await field_btn.click()   
									is_submit_success =  await is_navigate_success()
									if is_submit_success:
										SUBMIT_METHODS.insert(0,sub_method)
										# SUBMIT_BUTTON_INDEX = bt_ind 
										break
								except Exception as fe:
									print(fe)
								await pup_page.goto(curr_url, {'waitUntil':['networkidle2'],'timeout':900000 })
								await input_values(page_det, curr_url, captcha_results)
								print('Entered input values!!')	
								await asyncio.sleep(5)
						else:
							continue
						break

					if sub_method == 'link_button':
						field_links = await pup_page.JJ('a')
						
						for link_ind, link in enumerate(field_links):
							link_pos = await link.boundingBox()	
							print('link',link_pos,link)
							if await link.isIntersectingViewport():
								try:
									link_class = await pup_page.JJeval('a','all=> all['+str(link_ind)+'].getAttribute("class")')
									link_text = await pup_page.JJeval('a','all=> all['+str(link_ind)+'].innerText')
										
									if 'button' in link_class or 'btn' in link_class:
										event_logger.info('crawl_page_info(%s,%s): Link Info :: (class: %s, text: %s) ' %(str(count), curr_url, link_class,link_text))	
										#await link.click()   
										#is_submit_success =  await is_navigate_success()
										if is_submit_success:
											SUBMIT_METHODS.insert(0,sub_method)
											# SUBMIT_BUTTON_INDEX = bt_ind 
											break
								except Exception as fe:
									print(fe)
								#await pup_page.goto(curr_url, {'waitUntil':['networkidle2'],'timeout':900000 })
								#await input_values(page_det, curr_url, captcha_results)
								#print('Entered input values!!')	
								#await asyncio.sleep(5)
						else:
							continue
						break

					if sub_method == 'form_name' and form != None:
						
						field_submit = await pup_page.JJ('form[name="'+form+'"]')
						if len(field_submit)>0:								
							event_logger.info('crawl_page_info(%s,%s): Form Submitted by Name  :: (%s) ' %(str(count), curr_url, form ))

							await pup_page.Jeval('form[name="'+form+'"]', "(fm) =>{fm.submit();}") 									
							is_submit_success =  await is_navigate_success()
						else:
							sub_method = SUBMIT_METHODS.index(sub_method)+1

					if sub_method == 'form_id' and form_id != None:

						field_submit = await pup_page.JJ('form[id="'+form_id+'"]')							
						if len(field_submit)>0:								
							event_logger.info('crawl_page_info(%s,%s): Form Submitted by Id  :: (%s) ' %(str(count), curr_url, form_id ))
							await pup_page.Jeval('form[id="'+form_id+'"]', "(fm) =>{fm.submit();}") 
							is_submit_success =  await is_navigate_success()
						else:
							sub_method = SUBMIT_METHODS.index(sub_method)+1

					if sub_method == 'submit_button':

						field_submit = await pup_page.JJ('input[type="submit"]')
						if len(field_submit) > 0:								
							btn_pos = await field_submit[0].boundingBox()	
							event_logger.info('crawl_page_info(%s,%s): Submit Button Clicked by Position :: (%s, %s, %s, %s) ' %(str(count), curr_url, str(btn_pos['x']), str(btn_pos['y']), str(btn_pos['width']), str(btn_pos['height'])))
									
							await field_submit[0].click()
							is_submit_success =  await is_navigate_success()
						else:
							sub_method = SUBMIT_METHODS.index(sub_method)+1

					if sub_method == 'enter_submit':							

						await asyncio.sleep(5)							
						event_logger.info('crawl_page_info(%s,%s): Submitted by Enter ' %(str(count), curr_url ))
						await pup_page.keyboard.press('Enter')
						is_submit_success =  await is_navigate_success()
						
					if sub_method == 'canvas_click':

						field_submit = await pup_page.JJ('canvas')

						if len(field_submit) > 0:								
							btn_pos = await field_submit[0].boundingBox()	
							event_logger.info('crawl_page_info(%s,%s): Canvas Clicked by Position :: (%s, %s, %s, %s) ' %(str(count), curr_url, str(btn_pos['x']), str(btn_pos['y']), str(btn_pos['width']), str(btn_pos['height'])))
							await field_submit[0].click()							
							await field_submit[0].hover()								
							await field_submit[0].click()
							is_submit_success =  await is_navigate_success()
						else:
							sub_method = SUBMIT_METHODS.index(sub_method)+1

					if sub_method == 'path_click':
						field_submit = await pup_page.JJ('path')

						if len(field_submit) > 0:								
							btn_pos = await field_submit[0].boundingBox()	
							event_logger.info('crawl_page_info(%s,%s): Path Clicked by Position :: (%s, %s, %s, %s) ' %(str(count), curr_url, str(btn_pos['x']), str(btn_pos['y']), str(btn_pos['width']), str(btn_pos['height'])))
							await field_submit[0].click()							
							await field_submit[0].hover()								
							await field_submit[0].click()
							is_submit_success =  await is_navigate_success()
						else:
							sub_method = SUBMIT_METHODS.index(sub_method)+1

					if sub_method == 'input_image':
						field_submit = await pup_page.JJ('input[type="image"]')

						if len(field_submit) > 0:								
							btn_pos = await field_submit[0].boundingBox()	
							event_logger.info('crawl_page_info(%s,%s): Input Image Clicked by Position :: (%s, %s, %s, %s) ' %(str(count), curr_url, str(btn_pos['x']), str(btn_pos['y']), str(btn_pos['width']), str(btn_pos['height'])))
							await field_submit[0].click()								
							is_submit_success =  await is_navigate_success()
						else:
							sub_method = SUBMIT_METHODS.index(sub_method)+1

					if sub_method == 'gremlin_clicks':			
				
						await pup_page.evaluate("""() => { gremlins.createHorde({
							species: [gremlins.species.clicker({clickTypes:['click','mousedown','mouseup', 'mousemove', 'dblclick']})],
										
							mogwais: [gremlins.mogwais.alert(),gremlins.mogwais.fps(),gremlins.mogwais.gizmo()],								
							strategies: [gremlins.strategies.allTogether({delay: 500, nb: 1000 })]
						}).unleash() }"""
						)
						await asyncio.sleep(5)
							
						event_logger.info('crawl_page_info(%s,%s): Submit by Gremlin Clicks ' %(str(count), curr_url))
							
						is_submit_success =  await is_navigate_success()
						break

				except Exception as se:
					print(se)

				if is_submit_success:
					SUBMIT_METHODS.insert(0,sub_method)
					event_logger.info('crawl_page_info(%s,%s): Successfully submitted via %s ' %(str(count), curr_url, sub_method))
					break
		except Exception as se:
			print('Exception in submission', se)
	
	
	### Intercept and handle requests and responses from the pages
	
	#await pup_page.setRequestInterception(True)
	pup_page.on('request', lambda req: asyncio.ensure_future(handle_request(req)))
	pup_page.on('response',  lambda res: asyncio.ensure_future(handle_response(res)))

	await pup_page.evaluateOnNewDocument("()=> "+extra_scripts.js_add_event_override)
	pup_page.on('console', lambda t: asyncio.ensure_future(log_events_helper(t)))

 	### Visit the page 
	try:
		await asyncio.sleep(3)
		await pup_page.setViewport({'width':1366, 'height':768})
		event_logger.info('crawl_page_info(%s,%s) :: Visiting URL :: %s '%(str(count),phish_url, phish_url))
		await pup_page.goto(phish_url, {'waitUntil':['networkidle0', 'domcontentloaded'],'timeout':900000 })		
	except Exception as e:
		print(e)

	org_url = tldextract.extract(phish_url)
	is_run_complete = False 

	try:
		loop_count=0
		### Different methods to submit the data , prioritized from specific method to more generalized
		SUBMIT_METHODS = [ 'enter_submit','button', 'submit_button','link_button', 'visual_button', 'form_name', 'form_id',  'canvas_click', 'path_click', 'input_image']#, 'gremlin_clicks' ] 
		SUBMIT_BUTTON_INDEX =-1
		### Parse and Interact with the pages
		while loop_count<20:

			loop_count = loop_count+1
			try:

				### Saving screenshot of the current page before interaction
				path=dir_path+'/images/'+str(count)	
				if not os.path.exists(path):
					os.makedirs(path)
				if not os.path.exists(path+"/slices"):
					os.makedirs(path+"/slices")
				path_slice = path+"/slices/"+str(count)+'_'+str(page_count)+'_screenshot.png'
				path_full = path+"/"+str(count)+'_'+str(page_count)+'_screenshot_full.png'
				path= path+"/"+str(count)+'_'+str(page_count)+'_screenshot.png'
				
				path_content = dir_path+'/resources/'+str(count)+'_page_'+str(page_count)+'.html'
				
				### Wait for the page to load
				try:
					await pup_page.waitForNavigation({'waituntil':'networkidle2','timeout':30000})
				except Exception as te:
					logger.info('crawl_page_info(%s,%s): Navigation Timeout Exception!!'%(str(count), phish_url))

				try:
					await pup_page.screenshot({'path': path, 'fullPage':False})
					await pup_page.screenshot({'path': path_slice, 'fullPage':True})
					await pup_page.screenshot({'path': path_full, 'fullPage':True})
				except Exception as e:
					print(e)

				try:
					content = await pup_page.content()
					with open(path_content,'w') as fc:
						fc.write(content)
				except Exception as e:
					print(e)
					
				# try:
				# 	session = await pup_page.target.createCDPSession()
				# 	await session.send('Page.enable')
				# 	page_mhtml = await session.send('Page.captureSnapshot', {"format": "mhtml"})
				# 	with open(dir_path+'/resources/'+str(count)+"_"+str(page_count)+".mhtml", 'w') as fo:
				# 		fo.write(page_mhtml)
				# except Exception as me:
				# 	print(me)

				curr_url = pup_page.url			
				page_url = tldextract.extract(curr_url)  

				await pup_page.addScriptTag({'content': extra_scripts.js_dom_scripts})
				await asyncio.sleep(5)	

				### Get title of the page				
				title = await pup_page.evaluate("()=>get_title()")
				print('Crawling Page :: ',loop_count, ' :: ' , title)
				event_logger.info('crawl_page_info(%s,%s) :: Crawling Page ::{"page_count" : %s, "curr_url": %s , "title" : %s}'%(str(count),phish_url, loop_count,curr_url, title))
							
				### Get DOM details of the page				
				res = await pup_page.evaluate("()=> get_elements(document, -1)")

				### Get DOM Event Listeners of the page			
				await get_event_listeners()

				### Add Gremlin script to the page to be used later  
				await pup_page.addScriptTag({'url': 'https://unpkg.com/gremlins.js' })

				### Execute Script to override window open
				await pup_page.evaluate("()=>w_override(window,window.open)")

				### Clear any overlays by clicking on all buttons
				if loop_count==1:
					await clear_overlays()	

				### Get DOM tree to keep track of changes to the DOM
				dom_tree= await pup_page.evaluate("()=>get_dom_tree()")	
				# print(dom_tree)
				
				### Append page details to site
				page_image_det = str(count)+"_"+str(page_count)+'_screenshot.png'
				page = phish_db_schema.Pages(site_id = site_obj.site_id ,page_url = curr_url, page_title = title, page_image_id = page_image_det)		
				page.requests = page_requests
				
				page.responses = page_responses		
				page.dom_hash = get_dom_hash(dom_tree)
				event_logger.info('crawl_page_info(%s,%s) :: Page Details ::{"page_count" : %s, "page_image_id": %s, "curr_url": %s , "title" : %s, "dom_hash" : %s }'%(str(count),phish_url, loop_count, page_image_det, curr_url, title, page.dom_hash))
				# print(page.page_title, page.page_image_id)
				site_pages.append(page)

				### Continue execution even when page navigated to a different domain
				if org_url.domain != page_url.domain  and count > 0 and temp!=dom_tree :
					logger.info('crawl_page_info(%s,%s):  Navigated to different domain!!'%(str(count), curr_url))
					event_logger.info('crawl_page_info(%s,%s) :: Navigated to different domain!! ::{"page_count" : %s, "curr_url": %s }'%(str(count),phish_url, loop_count,curr_url))
					phish_db_layer.add_pages_to_site(site_obj.phish_tank_ref_id, site_pages, phish_url)
					is_run_complete = True
					return;
				await asyncio.sleep(5)

				### Check if the DOM structure is same as the previously visited page
				samePage = samePage+1 if temp==dom_tree else 0

				### If the same page was visited 3 times, then stop execution  		
				if samePage >= 3:
					phish_db_layer.add_pages_to_site(site_obj.phish_tank_ref_id, site_pages, phish_url)
					logger.info('crawl_page_info(%s,%s): Page repeated for few times!! ' %(str(count), curr_url))		
					event_logger.info('crawl_page_info(%s,%s) :: Page repeated for few times!! ::{"page_count" : %s, "prev_url": %s, "page_url": %s }'%(str(count),phish_url, loop_count,curr_url,page_url))
					is_run_complete = True
					return

				
				### Executes JS to detect known captchas and logs them
				await detect_known_captcha(page_image_det)

				### Identifies and takes screenshot of possible captcha elements
				# await get_noninput_elements(path_slice)
			
				temp = dom_tree				
				
				# print(res)
				### Parse and Categorize each elements in the page
				page = parse_elements(res,path_slice,page)
				
				
				### Check for Captchas and interact if found
				#captcha_results = await detect_captcha_visual(path)
				captcha_results = {}
				time.sleep(3)

				### Try submitting via multiple methods
				print('SUBMITTING STARTED!!!!!!!!!!!!!!!!!!!!!!!!!!!!!')				
				res_page_count = page_count + 1
				await submit_page(page, curr_url,captcha_results)
				# await 
				print('SUBMITTING COMPLETE!!!!!!!!!!!!!!!!!!!!!!!!!!!!!')

				
				try:
					print('Adding Page Info!!')
					phish_db_layer.add_page_info(page)
				except Exception as se:
					print(se)

				page_count = page_count+1			
				page_requests = []
				page_responses = []
				# await pup_page.reload()  		
				await asyncio.sleep(5)
			except Exception as e:
				print('Exception Occured',e)

	except Exception as oe:
		event_logger.info('crawl_page_info(%s,%s): Exception -- %s'%(str(count), phish_url, oe))
	finally:
		if not is_run_complete:
			phish_db_layer.add_pages_to_site(site_obj.phish_tank_ref_id ,site_pages, phish_url)
			event_logger.info('crawl_page_info(%s,%s): Crawling Complete!! Browser Closed!! ' %(str(count), phish_url))
		else:
			event_logger.info('crawl_page_info(%s,%s): Crawling Incomplete!! Browser Closed ' %(str(count), phish_url))
		await browser.close()
		
		print('Browser Closed!!!')


async def main(url, phish_id, time_out=1200):
	site_pages =[]
	site_obj = phish_db_schema.Sites(site_url = url, phish_tank_ref_id = phish_id)
	try:		
		site_obj = phish_db_layer.add_site_info(site_obj)
		event_logger.info('main(%s,%s):: Crawling Started!!' %(str(site_obj.site_id), url))
		# Starts the crawling process with a execution timeout
		await asyncio.wait_for( crawl_web_page(url, site_obj, site_pages,  phish_id), timeout = time_out)
	except asyncio.TimeoutError:
		print('timeout')
		phish_db_layer.add_pages_to_site(site_obj.phish_tank_ref_id ,site_pages, url)
		


parser = argparse.ArgumentParser(description="Crawl phishing links")
parser.add_argument('url', type=str, help= "URL to crawl")
parser.add_argument('--phish_id', default=9999 , help="Unique id from phishtank database(optional)" )
parser.add_argument('--timeout', default=1100, help="Time duration after which the program will terminate" )

if __name__ == '__main__':
	args = parser.parse_args()
	# print(args.url, args.phish_id, args.timeout)
	asyncio.get_event_loop().run_until_complete(main(args.url, args.phish_id, args.timeout))
