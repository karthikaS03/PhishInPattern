#!/usr/bin/python
# coding=utf8
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
			# print(r["tag"])
			# print('******************************Processing Element ::***********************************************')
		
			if any(tag in r["tag"] for tag in ['INPUT']) and 'type' in r and r["type"] not in ['hidden','button','submit','reset','radio','checkbox'] and r["visibility"]!='hidden':
				# print('******************************Processing Element ::***********************************************')
				# print(r)
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
					#print('Screenshot inner text: ',text)
					text = filterData(text)
					if len(text)>1 :    					
						element.parsed_texts.append(text)
						element.parsed_methods.append("Image_OCR_Read_Inside")
						element = add_InnerText(element)  					    
						flag=True if len(element.categories[-1])>1 else False       
	          
				if flag==False:           
					text=screenshot_slicing.img_to_text(path,'L',r["left"]-200,r["top"],r["left"],r["bottom"],3)
					#print(text)  
					text = filterData(text)  
					if len(text)>1 :      					
						element.parsed_texts.append(text)
						element.parsed_methods.append("Image_OCR_Read_Left")
						element = add_InnerText(element)                    	
						flag=True if len(element.categories[-1])>1 else False  
					else:          
						text=screenshot_slicing.img_to_text(path,'T',r["left"],r["top"]-(r["height"]+5),r["right"],r["bottom"]-(r["bottom"]-r["top"]),3)  
						#print('Screenshot result:',text)
						text = filterData(text)    
						if len(text)>1 :						
							element.parsed_texts.append(text)
							element.parsed_methods.append("Image_OCR_Read_Top")
							element = add_InnerText(element)                
							flag=True if len(element.categories[-1])>1 else False        
				if r["placeholder"]!='null' and flag!=True:      
					flag=True;
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
				# phish_db_layer.add_element_info(element_db)
				print('parse_elements(%s) Element ->  Name: %s ;  Html_Id: %s ; Category: %s ; Value: %s; Parsed_text: %s; Parsed_method:%s' % ( page.page_image_id,element.name, element.html_id,category,value,parsed_text,parsed_method))
	except Exception as pre:
		print('Parse_Elements :: Exception !! ',pre)	
	return page

def get_frame(frameIndex, pup_page):
	if frameIndex == -1:
		frame = pup_page
	else:
		frame = pup_page.frames[frameIndex+1]
	return frame

async def reset_element(element, page, field_selector):
	try:
		# await get_frame(element.element_frame_index, page).click()
		if  await element.getProperty("type") not in ["hidden","button","reset","a","checkbox","submit","radio"] and await element.isIntersectingViewport(): 
			# print('Resetting Element!!')	
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
		print('Reset Element!!', e)
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
							
							var e = document.getElementsByTagName('*');   
							for (var i=0; i<e.length; i++) {
								elements = elements+" "+e[i].tagName+";"							}
							
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
	js_mouse_pointer = """() => {
    // Install mouse helper only for top-level frame.
    if (window !== window.parent)
      return;
    window.addEventListener('DOMContentLoaded', () => {
      const box = document.createElement('puppeteer-mouse-pointer');
      const styleElement = document.createElement('style');
      styleElement.innerHTML = `
        puppeteer-mouse-pointer {
          pointer-events: none;
          position: absolute;
          top: 0;
          z-index: 10000;
          left: 0;
          width: 20px;
          height: 20px;
          background: rgba(0,0,0,.4);
          border: 1px solid white;
          border-radius: 10px;
          margin: -10px 0 0 -10px;
          padding: 0;
          transition: background .2s, border-radius .2s, border-color .2s;
        }
        puppeteer-mouse-pointer.button-1 {
          transition: none;
          background: rgba(0,0,0,0.9);
        }
        puppeteer-mouse-pointer.button-2 {
          transition: none;
          border-color: rgba(0,0,255,0.9);
        }
        puppeteer-mouse-pointer.button-3 {
          transition: none;
          border-radius: 4px;
        }
        puppeteer-mouse-pointer.button-4 {
          transition: none;
          border-color: rgba(255,0,0,0.9);
        }
        puppeteer-mouse-pointer.button-5 {
          transition: none;
          border-color: rgba(0,255,0,0.9);
        }
      `;
      document.head.appendChild(styleElement);
      document.body.appendChild(box);
      document.addEventListener('mousemove', event => {
        box.style.left = event.pageX + 'px';
        box.style.top = event.pageY + 'px';
        updateButtons(event.buttons);
      }, true);
      document.addEventListener('mousedown', event => {
        updateButtons(event.buttons);
        box.classList.add('button-' + event.which);
      }, true);
      document.addEventListener('mouseup', event => {
        updateButtons(event.buttons);
        box.classList.remove('button-' + event.which);
      }, true);
      function updateButtons(buttons) {
        for (let i = 0; i < 5; i++)
          box.classList.toggle('button-' + i, buttons & (1 << i));
      }
    }, false);
  }
	"""
	temp = None 
	samePage = 0
	count=phish_id
	res_count = 1
	page_count=0
	site_pages =[]
	page_requests = []
	page_responses = []

	async def is_same_page():
		try:
			time.sleep(5)
			dom_tree= await pup_page.evaluate(js_elements_tree)
			print('Is Same Page ::' , temp==dom_tree)
			return temp == dom_tree
		except Exception as e:
			print('is_same_page :: Exception ',e)

	async def clear_overlays():
		field_buttons = await pup_page.JJ('button')

		for field_btn in field_buttons:
			print('Button clicked')
			print((await field_btn.getProperty('name')).toString()  )
			if await field_btn.isIntersectingViewport():
				try:				
					await field_btn.click()   
				except Exception as fe:
					print(fe)

	async def handle_request(req):
		###
		### Intercept Page Requests and log them
		###

		req_url = req.url
		req_domain =  '.'.join(tldextract.extract(req_url)[1:]) 
		req_info = phish_db_schema.Page_Request_Info(request_url = req_url, request_domain = req_domain, request_method = req.method, request_type = req.resourceType)
		# phish_db_layer.add_page_req_info(req_info)
		page_requests.append(req_info)

		await req.continue_()

	async def handle_response(res):
		###
		### Fetch Responses, Store them and their hash in database 
		###

		res_name = (res.url.split('?')[0]).split('/')[-1]
		res_name = res_name if len(res_name)>1 else 'res_' + str(site_obj.site_id) + '_' + res_count
		res_count = res_count + 1
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

		rsp_info = phish_db_schema.Page_Response_Info(response_url = res.url, response_file_path = file_path, response_file_hash = digest)
		# phish_db_layer.add_page_rsp_info(rsp_info)
		page_responses.append(rsp_info)

	async def get_field(field_selector, frameIndex):
		try:
			frame = get_frame(frameIndex, pup_page)
			await frame.waitFor(field_selector)
			field = await frame.J(field_selector);
			form = await frame.Jeval(field_selector, "(el)=>{ return el.form.name }");
			form_id = await frame.Jeval(field_selector, "(el)=>{ return el.form.id }");
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
				logger.info('crawl_page_info(%s,%s): Providing input for Element (%s,%s,%s,%s) ' %(str(count),curr_url,element.element_name,element.element_html_id,element.element_tag,element.element_value))
				field = None		
				field_selector = ''				
				print('Element :: ', element)

				if 'Unknown' not in element.element_name and len(element.element_name)>0:	
					field_selector = 'input[name='+element.element_name+']'					
					field, form, form_id = await get_field(field_selector, element.element_frame_index)

				elif 'Unknown' not in element.element_id and len(element.element_id)>0:
					field_selector = 'input[id='+element.element_id+']'	
					field, form, form_id = await get_field(field_selector, element.element_frame_index)

				### Type the value in the field 
				if field !=None and await field.isIntersectingViewport(): 
					await reset_element(field, pup_page, field_selector)							
					print('typing value ::', element.element_value)
					# print(field)
					await field.focus()
					await field.type(element.element_value)
					time.sleep(3)
					await get_frame(element.element_frame_index, pup_page).Jeval(field_selector, "(el)=>{ el.blur(); }");
					time.sleep(3)

			except Exception as ve:
				print('Input Value!!', ve)
				logger.info('Input Value (%s,%s): Exception -> Failed on entering value ;%s' %(str(count), curr_url, str(ve)))
		
		return form, form_id

	### Intercept requests and responses from the pages
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
		### Parse and Interact with the pages
		while loop_count<20:

			loop_count = loop_count+1
			try:

				### Saving screenshot of the current page before interaction
				path=dir_path+'/images/'+str(count)		
				if not os.path.exists(path):
					os.makedirs(path)
				path= path+"/"+str(count)+'_'+str(page_count)+'_screenshot.png';
				try:
					await pup_page.screenshot({'path': path, 'fullPage':True})
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
				
				### Stop execution when page navigated to a different domain
				if org_url.domain != page_url.domain :
					logger.info('crawl_page_info(%s,%s):  Navigated to different domain!!'%(str(count), curr_url))
					phish_db_layer.add_pages_to_site(phish_id, site_pages, phish_url)
					is_run_complete = True
					return;
				time.sleep(5)
				### Get DOM details of the page
				await pup_page.addScriptTag({'content': js_domelements_position})
				res = await pup_page.evaluate("()=> get_elements(document, -1)")

				dom_tree= await pup_page.evaluate(js_elements_tree)	

				# print(dom_tree)
				### Check if the DOM structure is same as the previously visited page
				samePage = samePage+1 if temp==dom_tree else 0;

				### If the same page was visited 3 times, then stop execution  		
				if samePage >= 3:
					phish_db_layer.add_pages_to_site(phish_id, site_pages, phish_url)
					logger.info('crawl_page_info(%s,%s): Page repeated for few times!! ' %(str(count), curr_url))					
					is_run_complete = True
					return;

				### Clear any overlays by clinking on all buttons
				await clear_overlays()	
				
				time.sleep(15)

				temp = dom_tree
				form = None
				form_id = None
				
				### Parse and Categorize each elements in the page
				page = parse_elements(res,path,page)
				is_submit_success = False

				
				SUBMIT_METHODS = [ 'form_name', 'form_id', 'submit_button','button', 'enter_submit' ]

				### Try submitting via multiple methods
				for sub_method in SUBMIT_METHODS:

					print('Submitting method :: ', sub_method)
					form, form_id = await input_values(page, curr_url)
					time.sleep(5)
					print('Entered input values!!')

					try:
						if sub_method == 'button':
							field_buttons = await pup_page.JJ('button')
							for field_btn in field_buttons:
								await input_values(page,curr_url)
								time.sleep(5)
								print('Entered input values!!')
								
								
								await field_btn.focus()
								if await field_btn.isIntersectingViewport():
									try:					
										print('Button clicked')
										await field_btn.click()   
										is_submit_success = not await is_same_page()
										if is_submit_success:
											break
									except Exception as fe:
										print(fe)
								await pup_page.goto(curr_url, {'waitUntil':['networkidle0', 'domcontentloaded'],'timeout':900000 })
								
							else:
								continue
							break

						if sub_method == 'form_name':
							field_submit = await pup_page.JJ('form[name="'+form+'"]')
							if len(field_submit)>0:								
								print('form submitted by name')
								await pup_page.Jeval('form[name="'+form+'"]', "(fm) =>{fm.submit();}") 									
								is_submit_success = not await is_same_page()
							else:
								sub_method = SUBMIT_METHODS.index(sub_method)+1

						if sub_method == 'form_id':
							field_submit = await pup_page.JJ('form[id="'+form_id+'"]')
							if len(field_submit)>0:
								# form, form_id = await input_values(page, curr_url)
								# time.sleep(5)
								# print('Entered input values!!')
								print('form submitted by id')
								await pup_page.Jeval('form[id="'+form_id+'"]', "(fm) =>{fm.submit();}") 
								is_submit_success = not await is_same_page()
							else:
								sub_method = SUBMIT_METHODS.index(sub_method)+1

						if sub_method == 'submit_button':
							field_submit = await pup_page.JJ('input[type="submit"]')
							if len(field_submit) > 0:
								# form, form_id = await input_values(page, curr_url)
								# time.sleep(5)
								# print('Entered input values!!')
								print('submit button clicked!!')
								await field_submit[0].click()
								is_submit_success = not await is_same_page()
							else:
								sub_method = SUBMIT_METHODS.index(sub_method)+1

						if sub_method == 'enter_submit':
							form, form_id = await input_values(page, curr_url)
							time.sleep(5)
							print('Entered input values!!')
							print('Pressed Enter!!')
							await pup_page.keyboard.press('Enter')
							is_submit_success = not await is_same_page()
							break
					except Exception as se:
						print(se)

					if is_submit_success:
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
			phish_db_layer.add_pages_to_site(phish_id,site_pages, phish_url)

async def main(url, phish_id):

	try:
		site_obj = phish_db_schema.Sites(site_url = url, phish_tank_ref_id = phish_id)
		site_obj = phish_db_layer.add_site_info(site_obj)
		# print(site_obj)
		# Starts the crawling process with a execution timeout
		await asyncio.wait_for( crawl_web_page(url, site_obj, phish_id), timeout = 600)
	except asyncio.TimeoutError:
		print('timeout')


parser = argparse.ArgumentParser(description="Crawl phishing links")
parser.add_argument('url', type=str, help= "URL to crawl")
parser.add_argument('--phish_id', default=-1, help="Unique id from phishtank database(optional)" )

if __name__ == '__main__':
	args = parser.parse_args()
	print(args.url, args.phish_id)
	asyncio.get_event_loop().run_until_complete(main(args.url, args.phish_id))