
import sys
import os
import asyncio
from pyppeteer import launch
import argparse
import time
from pprint import pprint
import screenshot_slicing
import extra_scripts

async def crawl_web_page(phish_url):

    browser = await launch({ 'headless':False, 'args': [                             
                                '--no-sandbox',
                                '--disable-setuid-sandbox',                               
                                '--start-maximized',
                                '--ignore-certificate-errors'
                                ]
                            })

    async def handle_target(t):
        # print('target created')
        # print(t.type)
        if t.type =='page':
            p = await t.page()
            # print(p)
            await p.evaluate("""()=>{alert('page  opened!!!')}""")
            # await p.addScriptTag({'content':extra_scripts.js_add_event_override})
            # await p.evaluateOnNewDocument("()=> load_scripts()")

    browser.on('targetcreated', lambda t: asyncio.ensure_future(handle_target(t)))

    pup_page = await browser.newPage()

    async def get_noninput_elements(): 

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
        try:
            await pup_page.screenshot({'path': 'test.png'})
        except Exception as e:
            print(e)

        for i,f in enumerate(pup_page.frames):
            await f.addScriptTag({'content': js_all_elements})
            frame_elements = await f.evaluate("()=> process_elements(document.body)")
            
            for fe in frame_elements:
                fe['frame_no'] = i
                all_elements.append(fe)            
            # all_elements.extend(frame_elements)
        all_elements.sort(key = lambda x: x['size'], reverse = True)
        
        ignore_tags = ['INPUT', 'A', 'SCRIPT', 'LI', 'UL', 'FORM']
        for i,el in enumerate(all_elements):
            dim = list(map(float,el['dimension'].split(';'))) if len(el['dimension'])>0 else None
            if el['tag'] not in ignore_tags and el['size']>15000 and dim!=None and dim[4]<150:
                screenshot_slicing.img_to_text('test.png', str(i)+'_'+str(el['size'])+'_'+el['tag'], dim[0], dim[2], dim[1], dim[3] , 3)

        pprint(all_elements)

    
    async def detect_known_captcha():       

        for i,f in enumerate(pup_page.frames):
            print(i)
            await f.addScriptTag({'content':extra_scripts.js_captchas})

            captcha_methods = [" findRecaptchaClients()", " find_recaptcha()", " find_hcaptcha()", " find_keycaptcha()"]
            for cm in captcha_methods:
                captcha_details = await f.evaluate("""()=>"""+cm)
                print(captcha_details)

            # captcha_details = await f.evaluate("""()=> findRecaptchaClients()""")
            # print(captcha_details)

            # captcha_details = await f.evaluate("""()=> find_recaptcha()""")
            # print(captcha_details)

            # # await pup_page.addScriptTag({'content':js_hcaptcha})
            # captcha_details = await f.evaluate("""()=> find_hcaptcha()""")
            # # print(captcha_details)

            # captcha_details = await f.evaluate("""()=> find_keycaptcha()""")
            # print(captcha_details)

    async def get_event_listeners() :

        session = await pup_page.target.createCDPSession()

        res = await session.send('Runtime.evaluate', {
        "expression" : "document.querySelectorAll('*')"
        })
        

        result = await session.send('Runtime.getProperties', {'objectId' : res['result']['objectId']}) ; 
       
        descriptors= list(filter(lambda x:  x.get('value', None) != None and x['value'].get('objectId', None) !=None and x['value'].get('className',None) != 'Function' , result['result']))
        # print(descriptors)

        elements = []
        # await session.send('DOMSnapshot.enable')
        # snapshots = await session.send('DOMSnapshot.captureSnapshot', 'c')
        # print(snapshots)
        for descriptor  in descriptors:
            objectId = descriptor['value']['objectId']
            ## Add the event listeners, and description of the node (for attributes)
            all_listeners = await session.send('DOMDebugger.getEventListeners', {'objectId' : objectId })
            node_desc = await session.send('DOM.describeNode', { 'objectId' : objectId })
            
            
            # node_det  = await session.send('DOM.pushNodesByBackendIdsToFrontend', { 'backendNodeIds' : [node_desc['node']['backendNodeId']] })
            # print(node_det)
            if len(all_listeners['listeners']) > 0:
                elements.append({'node' : node_desc['node'], 'listeners': all_listeners['listeners'] })

        print(elements)
        return elements

    async def log_events_helper(log):
        print('Log Triggered ::', log.text)
        return

    ### Visit the page 
    try:
        await asyncio.sleep(3)
        await pup_page.setViewport({'width':1366, 'height':768})
        # await pup_page.addScriptTag({'content':extra_scripts.js_add_event_override})
        # await pup_page.evaluateOnNewDocument("()=> load_scripts()")
        await pup_page.evaluateOnNewDocument("()=> "+extra_scripts.js_add_event_override)
           
        # await asyncio.sleep(20)
        await pup_page.goto(phish_url, {'waitUntil':['networkidle0', 'domcontentloaded'],'timeout':900000 })
        # await pup_page.addScriptTag({'content':extra_scripts.js_add_event_override})
        # await pup_page.evaluate("()=> load_scripts()")
        await asyncio.sleep(10)
        # await pup_page.reload()
        await asyncio.sleep(10)
 
        count = 1
        pup_page.on('console', lambda t: asyncio.ensure_future(log_events_helper(t)))
        
        while True:
            print('Page visit ::', count)
            try:
                await pup_page.waitForNavigation({'waituntil':'networkidle2','timeout':15000})
            except Exception as ex:
                print('navigation timeout!!!')

            print(pup_page, pup_page.frames)
            
            # await pup_page.exposeFunction('log_events_helper',log_events_helper)
            for i,f in enumerate(pup_page.frames):
                print('frame processed')                
                await f.addScriptTag({'content':extra_scripts.js_event_scripts})
                all_listeners = await f.evaluate("()=> listAllEventListeners()")
                

            print('Page visit Ended ::', count)
            # await asyncio.sleep(10)
            
            # while True:
            #     count += 1
        

    except Exception as e:
        print(e)

    # await get_noninput_elements()
    # await detect_known_captcha()
    # await get_event_listeners()
    await asyncio.sleep(100)
    print('Sleep Ended')
    # await asyncio.sleep(1000)

async def main(url):

	try:		
		# Starts the crawling process with a execution timeout
		await asyncio.wait_for( crawl_web_page(url), timeout=300)
	except asyncio.TimeoutError:
		print('timeout')


if __name__ == '__main__':
	
	test_url = 'https://www.google.com/recaptcha/api2/demo'
    # 'https://2captcha.com/demo/keycaptcha'
    # 'https://www.google.com/recaptcha/api2/demo'
    # 'https://recaptcha-demo.appspot.com/recaptcha-v2-checkbox.php'
    # 'http://democaptcha.com/demo-form-eng/hcaptcha.html'
	asyncio.get_event_loop().run_until_complete(main(test_url))
