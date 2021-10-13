
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
import page_element
import time
import MNB_field_classifier
import tldextract
import argparse

dir_path = os.path.abspath(os.path.dirname(__file__))
dir_path = dir_path +'/../../data'

logger = Phish_Logger.get_phish_logger('page_crawler.py')

textTags=['DIV','SPAN','TD','LABEL','H1','H2','H3','P','STRONG']

password = None

#### MAIN ####
def add_InnerText(element):	
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
	
	return element;

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
	try:
		fields=[];
		elementCount=0
		#Enumerate all the elements in the page
		for index,r in enumerate(res):
			#Filter Input and Select tags which are not hidden

			if any(tag in r["tag"] for tag in ['INPUT']) and 'type' in r and r["type"] not in ['hidden','button','submit','reset','radio','checkbox'] and r["visibility"]!='hidden':
				
				flag=False;
				elementCount=elementCount+1;
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

				#print "Element" + r["name"]
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
								break;          
					elif abs(itm["top"] - r["top"])<15 and abs(itm["left"]-r["left"])<5 and any(tag in itm["tag"] for tag in textTags):
						if itm["innerText"] !=None:	  		
							text = filterData(itm["innerText"])				
							#print "top" +itm["innerText"]
							if len(text)>1 and len(text)<35 :							
								element.parsed_texts.append(text)
								element.parsed_methods.append("TopSide_InnerText")
								element = add_InnerText(element)           
								flag=True if len(element.categories[-1])>1 else False
								break;
				if flag==False:           
					text=screenshot_slicing.img_to_text(path,'I',r["left"]-5,r["top"]-5,r["right"]+5,r["bottom"]+5,3) 
					
					text = filterData(text)
					if len(text)>1 :    					
						element.parsed_texts.append(text)
						element.parsed_methods.append("Image_OCR_Read_Inside")
						element = add_InnerText(element)  					    
						flag=True if len(element.categories[-1])>1 else False       
	          
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
				if r["placeholder"]!='null' and flag!=True:      
					flag=True
					element.parsed_texts.append(r["placeholder"])
					element.parsed_methods.append("placeholder")
					element = add_InnerText(element)
				category, value, parsed_text, parsed_method = element.get_category_value()
				logger.info('parse_elements(%s) Element ->  Name: %s ;  Html_Id: %s ; Category: %s ; Value: %s; Parsed_text: %s; Parsed_method:%s' % ( page.page_image_id,element.name, element.html_id,category,value,parsed_text,parsed_method))
				category_id = phish_db_layer.find_category_id(category)
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
		print('Parse_Elements :: Exception !! ',pre)	
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
			while cnt <= 50:
				await element.press('Backspace')
				cnt = cnt+1
			# await page.keyboard.down('Control');
			# await page.keyboard.press('A');
			# await page.keyboard.up('Control');
			# await page.keyboard.press('Backspace');
			# await page.keyboard.press('Enter')
	except Exception as e:
		
		logger.info('reset_element(): Exception!!') 

async def crawl_web_page(phish_url,site_obj, phish_id=-1):

	browser = await launch({ 'headless':False, 'args': [                             
	                            '--no-sandbox',
	                            '--disable-setuid-sandbox',                               
	                            '--start-maximized',
	                            '--ignore-certificate-errors'
	                           ]
	                     })
	 

	pup_page = await browser.newPage()

	### Javscript code to read the elements in a page, their properties and co-ordinates 
	js_elements_tree       = """  ()=>{ 
							var elements ='';
							
							var e = document.querySelectorAll('input, div, button, span, label');   
							for (var i=0; i<e.length; i++) {
								elements = elements+" "+e[i].tagName+"("+e[i].getBoundingClientRect().height+");"
							}
							
							return elements; }
							"""
	js_domelements_position = """function get_elements(el, frameIndex){  
							var tags = [];
							var recs = [];   
							var iframe_count = 0 
							width  =Math.max(document.body.scrollWidth, document.body.offsetWidth, document.documentElement.clientWidth, document.documentElement.scrollWidth, document.documentElement.offsetWidth)
							if(el==null) return recs;
							var e = el.getElementsByTagName('*');   
							for (var i=0; i<e.length; i++) {
								var rect           = e[i].getBoundingClientRect();
								
								recs[i]={}
								if (rect != undefined){
									recs[i].right = rect.right;
									recs[i].top = rect.top;
									recs[i].bottom = rect.bottom;
									recs[i].left = rect.left
									recs[i].height = rect.height
								}
								recs[i].innerText  = e[i].textContent ;        
								recs[i].tag        = e[i].tagName!= undefined? e[i].tagName : '';
								recs[i].id         = e[i].id!=null?e[i].id:'None';
								recs[i].name       = e[i].name!=null?e[i].name:'None';
								recs[i].type       = e[i].type ;
								recs[i].text       = e[i].Text ;
								recs[i].value      = e[i].value ;
								//recs[i].left       = (e[i].clientLeft/document.documentElement.clientWidth )* width;        
								recs[i].visibility = e[i].style!= undefined ? e[i].style.visibility : 'null' ;
								recs[i].placeholder= e[i].placeholder!=null?e[i].placeholder!=''?e[i].placeholder:'null':'null';
								recs[i].form = 'Null'
								recs[i].frameIndex = frameIndex
								if (e[i].tagName =='IFRAME')
								{
									
									frame_elements = get_elements (e[i].contentDocument, iframe_count)
									recs = recs.concat(frame_elements)
									iframe_count = iframe_count + 1
								}								
							}
							return recs; }
							"""
	js_targeted_brands="""()=>{
					  title  = document.title;
					  return title;
					  }"""


	js_override_window_open ="""function w_override(window, open) {
													window.open = (url) => {
													open.call(window, url, '_self')
													}
								}"""

	temp = None 
	samePage = 0
	count=phish_id
	res_count = 1
	page_count=0
	site_pages =[]
	page_requests = []
	page_responses = []

	async def is_navigate_success():
		try:
			# time.sleep(3)
			try:
				await pup_page.waitForNavigation({'waituntil':'networkidle2','timeout':15000})
			except Exception as ex:
				print('navigation timeout!!!')
			dom_tree= await pup_page.evaluate(js_elements_tree) 			
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
		time.sleep(10)

	async def get_noninput_elements(screenshot_path): 

		###
		### javascript code to calculate size of all elements in the page and sort them in decreasing manner
		### Returns poisiton of the element with the size and tag 
		###

		js_all_elements = """ 
        
            element_details = []

            function get_elements(elems, parent_node_pos){
                var children_size = 0
                for (var i=0 ; i <elems.length;){
                
                    let el = elems[i]
                    console.log(el)
                    if (el == null){
                        i++
                        continue
                    }
                    var rect = el.getBoundingClientRect();
								
                    var dimensions = ''
                    if (rect != undefined){
                        dimensions = rect.left +';' + rect.right +';' +
                                     rect.top + ';' + rect.bottom + ';' +
                                     rect.height
                    }
                    let elem_det = {'pos': parent_node_pos +'_' + i,
                                    'tag': el.tagName,
                                    'size': el.clientWidth * el.clientHeight,
                                    'dimension': dimensions
                                    }
    
                    console.log(elem_det['pos'], '>>>  =================== >>>')              
                    children_size = children_size+ elem_det['size']                
                    console.log(elem_det)
                    if(el.children.length>0){
                        console.log(elem_det['pos'], el.children)
                        let child_size =  get_elements(el.children, elem_det['pos'])
                        console.log(elem_det['pos'], child_size)
                        elem_det['size'] = elem_det['size'] - child_size
                    
                    
                    }
                    console.log(elem_det)
                    console.log(elem_det['pos'], ' <<< ********************** <<<')
                    element_details.push(elem_det)
                    i++
            
                }
                return children_size

            }

            function process_elements(parent_element){
                get_elements(parent_element.children, 0)
                //element_details = element_details.sort((a,b) => (a.size > b.size))
                return element_details
            } 
        """

		all_elements = []
		

		for i,f in enumerate(pup_page.frames):
			await f.addScriptTag({'content': js_all_elements})
			frame_elements = await f.evaluate("()=> process_elements(document.body)")
			
			for fe in frame_elements:
				fe['frame_no'] = i
				all_elements.append(fe)            
			
		all_elements.sort(key = lambda x: x['size'], reverse = True)

		ignore_tags = ['INPUT', 'A', 'SCRIPT', 'LI', 'UL', 'FORM']
		for i,el in enumerate(all_elements):
			dim = list(map(float,el['dimension'].split(';'))) if len(el['dimension'])>0 else None
			if el['tag'] not in ignore_tags and el['size']>15000 and dim!=None and dim[4]<150:
				screenshot_slicing.img_to_text(screenshot_path, 'captcha_'+str(i)+'_'+str(el['size'])+'_'+el['tag'], dim[0], dim[2], dim[1], dim[3] , 3)

        

	async def handle_request(req):
		###
		### Intercept Page Requests and log them
		###

		def log_request_details(rq):
			req_url = rq.url
			req_domain =  '.'.join(tldextract.extract(req_url)[1:]) 
			req_info = phish_db_schema.Page_Request_Info(request_url = req_url, 
														request_domain = req_domain, 
														request_method = rq.method, 
														request_type = rq.resourceType
														,req_id = rq._requestId,
														post_data = rq.postData[:1990] if rq.postData !=None else rq.postData,
														headers = str(rq.headers)[:10000] if rq.headers !=None else rq.headers
														)

		
			# phish_db_layer.add_page_req_info(req_info)
			# print(rq.url,rq.postData)
			page_requests.append(req_info)
		
		log_request_details(req)

		
		
		### log details of requests involved in the redirections
		for r in req.redirectChain:
			log_request_details(r)
		
		await req.continue_()

	async def handle_response(res ):
		###
		### Fetch Responses, Store them and their hash in database 
		###
		
		res_name = (res.url.split('?')[0]).split('/')[-1]
		res_name = res_name if len(res_name)>1 else 'res_' + str(site_obj.site_id) + '_' + res.request._requestId
		# res_count = res_count + 1
		dpath = dir_path + '/resources/' + str(count)		
		digest = ''

		if not os.path.exists(dpath):
			os.makedirs(dpath)
		
		file_path = dpath + "/" + res_name 
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
			logger.info('handle_response: Exception!! ::'+res.url+' :: '+str(e))

		rsp_info = phish_db_schema.Page_Response_Info(	response_url = res.url, 
														response_file_path = file_path, 
														response_file_hash = digest,
														response_status = str(res.status),
														response_headers = str(res.headers)[:10000] if res.headers !=None else res.headers
													)
		# phish_db_layer.add_page_rsp_info(rsp_info)
		page_responses.append(rsp_info)

	async def is_field_visible(el):
		l,t,r,b = map(float,el.element_position.split(';'))
		if (r-l>0 and b-t >0) or await el.isIntersectingViewport():
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
			await frame.waitFor(field_selector)
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
							
	async def input_values(curr_page, curr_url):
		###
		### Iterate through each element and provide respective input
		###

		form = None 
		form_id = None
		field_selector = ''
		if curr_page.elements== None:
			return form,form_id


		for element in curr_page.elements:
			try:
				# print(element, is_field_visible(element))
				fv = await is_field_visible(element)
				if not fv:
					continue
				logger.info('crawl_page_info(%s,%s): Providing input for Element (%s,%s,%s,%s) ' %(str(count),curr_url,element.element_name,element.element_html_id,element.element_tag,element.element_value))
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
			
		return form, form_id

	def get_dom_hash(d_tree):
		hasher = hashlib.md5(d_tree.encode())
		return hasher.hexdigest()

	### Intercept and handle requests and responses from the pages
	await pup_page.setRequestInterception(True)
	pup_page.on('request', lambda req: asyncio.ensure_future(handle_request(req)))
	pup_page.on('response',  lambda res: asyncio.ensure_future(handle_response(res)))

 	### Visit the page 
	try:
		time.sleep(3)
		await pup_page.setViewport({'width':1366, 'height':768})
		await pup_page.goto(phish_url, {'waitUntil':['networkidle0', 'domcontentloaded'],'timeout':900000 })		
	except Exception as e:
		print(e)


	org_url = tldextract.extract(phish_url)
	is_run_complete = False 

	try:
		loop_count=0
		### Different methods to submit the data , prioritized from specific method to more generalized
		SUBMIT_METHODS = ['button', 'submit_button', 'form_name', 'form_id',  'canvas_click','path_click', 'enter_submit']#, 'gremlin_clicks' ] 
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
				path_slice = path+"/slices/"+str(count)+'_'+str(page_count)+'_screenshot.png';
				path= path+"/"+str(count)+'_'+str(page_count)+'_screenshot.png';
				
				try:
					await pup_page.screenshot({'path': path})#, 'fullPage':True})
					await pup_page.screenshot({'path': path_slice})#, 'fullPage':True})
				except Exception as e:
					print(e)

				### Wait for the page to load
				try:
					await pup_page.waitForNavigation({'timeout':30000})
				except Exception as te:
					logger.info('crawl_page_info(%s,%s): Navigation Timeout Exception!!'%(str(count), phish_url))

				
				curr_url = pup_page.url			
				page_url = tldextract.extract(curr_url)  

				### Get title of the page
				time.sleep(3)							
				title = await pup_page.evaluate(js_targeted_brands)
				print('Crawling Page :: ',loop_count, ' :: ' , title)

				### Append page details to site
				page = phish_db_schema.Pages(site_id = site_obj.site_id ,page_url = curr_url,page_title = title, page_image_id = str(count)+"_"+str(page_count)+'_screenshot.png')		
				page.requests = page_requests
				page.responses = page_responses		
				site_pages.append(page)
				
				### Continue execution even when page navigated to a different domain
				if org_url.domain != page_url.domain :
					logger.info('crawl_page_info(%s,%s):  Navigated to different domain!!'%(str(count), curr_url))
					phish_db_layer.add_pages_to_site(site_obj.phish_tank_ref_id, site_pages, phish_url)
					# is_run_complete = True
					# return;
				time.sleep(5)
				
				### Get DOM details of the page
				await pup_page.addScriptTag({'content': js_domelements_position})
				res = await pup_page.evaluate("()=> get_elements(document, -1)")
				
				### Add Gremlin script to the page to be used later  
				await pup_page.addScriptTag({'url': 'https://unpkg.com/gremlins.js' })

				### Execute Script to override window open
				await pup_page.addScriptTag({'content': js_override_window_open})
				await pup_page.evaluate("()=>w_override(window,window.open)")

				### Clear any overlays by clicking on all buttons
				if loop_count==1:
					await clear_overlays()	

				### Get DOM tree to keep track of changes to the DOM
				dom_tree= await pup_page.evaluate(js_elements_tree)	
				# print(dom_tree)
				page.dom_hash = get_dom_hash(dom_tree)
				print(page.dom_hash)

				### Check if the DOM structure is same as the previously visited page
				samePage = samePage+1 if temp==dom_tree else 0;

				### If the same page was visited 3 times, then stop execution  		
				if samePage >= 3:
					phish_db_layer.add_pages_to_site(site_obj.phish_tank_ref_id, site_pages, phish_url)
					logger.info('crawl_page_info(%s,%s): Page repeated for few times!! ' %(str(count), curr_url))					
					is_run_complete = True
					return

				
				
				await get_noninput_elements(path_slice)

				temp = dom_tree
				form = None
				form_id = None
				
				### Parse and Categorize each elements in the page
				page = parse_elements(res,path_slice,page)
				is_submit_success = False
				
				### Try submitting via multiple methods
				for sub_method in SUBMIT_METHODS:

					print('Submitting method :: ', sub_method)
					form, form_id = await input_values(page, curr_url)
					time.sleep(5)
					print('Entered input values!!')

					try:
						if sub_method == 'button':
							field_buttons = await pup_page.JJ('button')
							
							for bt_ind, field_btn in enumerate(field_buttons):
								btn_pos = await field_btn.boundingBox()		
								await field_btn.focus()

								if btn_pos!=None and btn_pos['width']>0 and btn_pos['height']>0 and  await field_btn.isIntersectingViewport():
									try:					
										print('Button clicked')
										await field_btn.click()   
										is_submit_success =  await is_navigate_success()
										if is_submit_success:
											SUBMIT_METHODS.insert(0,sub_method)
											# SUBMIT_BUTTON_INDEX = bt_ind 
											break
									except Exception as fe:
										print(fe)
									await pup_page.goto(curr_url, {'waitUntil':['networkidle2'],'timeout':900000 })
									await input_values(page,curr_url)
									print('Entered input values!!')	
									time.sleep(5)
							else:
								continue
							break

						if sub_method == 'form_name':
							field_submit = await pup_page.JJ('form[name="'+form+'"]')
							if len(field_submit)>0:								
								print('form submitted by name')
								await pup_page.Jeval('form[name="'+form+'"]', "(fm) =>{fm.submit();}") 									
								is_submit_success =  await is_navigate_success()
							else:
								sub_method = SUBMIT_METHODS.index(sub_method)+1

						if sub_method == 'form_id':
							field_submit = await pup_page.JJ('form[id="'+form_id+'"]')
							
							if len(field_submit)>0:								
								print('form submitted by id')
								await pup_page.Jeval('form[id="'+form_id+'"]', "(fm) =>{fm.submit();}") 
								is_submit_success =  await is_navigate_success()
							else:
								sub_method = SUBMIT_METHODS.index(sub_method)+1

						if sub_method == 'submit_button':
							field_submit = await pup_page.JJ('input[type="submit"]')
							if len(field_submit) > 0:								
								print('submit button clicked!!')
								await field_submit[0].click()
								is_submit_success =  await is_navigate_success()
							else:
								sub_method = SUBMIT_METHODS.index(sub_method)+1

						if sub_method == 'enter_submit':							
							time.sleep(5)							
							print('Pressed Enter!!')
							await pup_page.keyboard.press('Enter')
							is_submit_success =  await is_navigate_success()
							
						if sub_method == 'canvas_click':
							field_submit = await pup_page.JJ('canvas')

							if len(field_submit) > 0:								
								print('canvas found!! To be  clicked!!')
								await field_submit[0].click()								
								print('Canvas::  Hover over and click!!')
								await field_submit[0].hover()								
								await field_submit[0].click()
								is_submit_success =  await is_navigate_success()
							else:
								sub_method = SUBMIT_METHODS.index(sub_method)+1

						if sub_method == 'path_click':
							field_submit = await pup_page.JJ('path')

							if len(field_submit) > 0:								
								print('Path found!! To be  clicked!!')
								await field_submit[0].click()								
								print('Path::  Hover over and click!!')
								await field_submit[0].hover()								
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
							time.sleep(5)
							is_submit_success =  await is_navigate_success()
							break

					except Exception as se:
						print(se)

					if is_submit_success:
						SUBMIT_METHODS.insert(0,sub_method)
						logger.info('crawl_page_info(%s,%s): Successfully submitted!! ' %(str(count), curr_url))
						break

				### Saving a screenshot of the current page after entering field values
				if not os.path.exists(path):
					os.makedirs(path)
				path = dir_path+'/images/'+str(count)+"/"+str(count)+'_'+str(page_count)+'_processed_screenshot.png'
				try:
					await pup_page.screenshot({'path':path, 'fullPage': True})
				except Exception as se:
					logger.info('crawl_page_info(%s,%s): Exception -> Failed on saving processed screenshot; %s' %(str(count), curr_url, str(se)))

				try:
					print('Adding Page Info!!')
					phish_db_layer.add_page_info(page)
				except Exception as se:
					print(se)

				page_count = page_count+1			
				page_requests = []
				page_responses = []
				# await pup_page.reload()  		
				time.sleep(5)
			except Exception as e:
				print('Exception Occured',e)
			
	finally:
		await browser.close()
		print('Browser Closed!!!')
		if not is_run_complete:
			phish_db_layer.add_pages_to_site(site_obj.phish_tank_ref_id ,site_pages, phish_url)

async def main(url, phish_id, time_out=600):

	try:
		site_obj = phish_db_schema.Sites(site_url = url, phish_tank_ref_id = phish_id)
		site_obj = phish_db_layer.add_site_info(site_obj)
		print(site_obj)		
		# Starts the crawling process with a execution timeout
		await asyncio.wait_for( crawl_web_page(url, site_obj, phish_id), timeout = time_out)
	except asyncio.TimeoutError:
		print('timeout')


parser = argparse.ArgumentParser(description="Crawl phishing links")
parser.add_argument('url', type=str, help= "URL to crawl")
parser.add_argument('--phish_id', default=-1, help="Unique id from phishtank database(optional)" )
parser.add_argument('--timeout', default=600, help="Time duration after which the program will terminate" )

if __name__ == '__main__':
	args = parser.parse_args()
	print(args.url, args.phish_id, args.timeout)
	asyncio.get_event_loop().run_until_complete(main(args.url, args.phish_id, args.timeout))