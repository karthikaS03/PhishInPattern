js_captchas = """
                    function findRecaptchaClients() {
                        // eslint-disable-next-line camelcase
                        if (typeof (___grecaptcha_cfg) !== 'undefined') {
                            // eslint-disable-next-line camelcase, no-undef
                            return Object.entries(___grecaptcha_cfg.clients).map(([cid, client]) => {
                            const data = { id: cid, version: cid >= 10000 ? 'V3' : 'V2' };
                            const objects = Object.entries(client).filter(([_, value]) => value && typeof value === 'object');

                            objects.forEach(([toplevelKey, toplevel]) => {
                                const found = Object.entries(toplevel).find(([_, value]) => (
                                value && typeof value === 'object' && 'sitekey' in value && 'size' in value
                                ));
                                if (found) {
                                const [sublevelKey, sublevel] = found;

                                data.sitekey = sublevel.sitekey;
                                const callbackKey = data.version === 'V2' ? 'callback' : 'promise-callback';
                                const callback = sublevel[callbackKey];
                                if (!callback) {
                                    data.callback = null;
                                    data.function = null;
                                } else {
                                    data.function = callback;
                                    const keys = [cid, toplevelKey, sublevelKey, callbackKey].map((key) => `['${key}']`).join('');
                                    data.callback = `___grecaptcha_cfg.clients${keys}`;
                                }
                                }
                            });
                            return data;
                            });
                        }
                        return [];
                    }
                    
                    function find_recaptcha(){
                        var captcha_el = document.getElementsByClassName('recaptcha')
                        if (captcha_el!=null && captcha_el.length>0){
                            if( captcha_el[0].hasAttribute('data-sitekey'))
                                return {'sitekey':  captcha_el[0].getAttribute('data-sitekey')}
                        }
                        return {}
                    }

                    function find_hcaptcha(){
                        var captcha_el = document.getElementsByClassName('h-captcha')
                        if (captcha_el!=null && captcha_el.length>0){
                            if( captcha_el[0].hasAttribute('data-sitekey'))
                                return {'sitekey':  captcha_el[0].getAttribute('data-sitekey')}
                        }
                        return {}
                    }

                    function find_keycaptcha(){
                        try{
                            return {s_s_c_user_id, s_s_c_session_id, s_s_c_web_server_sign, s_s_c_web_server_sign2}
                        }catch(error){
                            return {}
                        }
                    }
                """


### Javscript code to read the elements in a page, their properties and co-ordinates 

js_dom_scripts = """ 
        
            element_details = []

            function get_child_elements(elems, parent_node_pos){
                var children_size = 0
                for (var i=0 ; i <elems.length;){
                    let el = elems[i]
                    //console.log(el)
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
                                    'dimension': dimensions,
									'class': el.getAttribute('class')
                                    }
    
                    //console.log(elem_det['pos'], '>>>  =================== >>>')              
                    children_size = children_size+ elem_det['size']                
                    //console.log(elem_det)
                    if(el.children.length>0){
                        //console.log(elem_det['pos'], el.children)
                        let child_size =  get_child_elements(el.children, elem_det['pos'])
                        //console.log(elem_det['pos'], child_size)
                        elem_det['size'] = elem_det['size'] - child_size                    
                    }
                    //console.log(elem_det)
                    //console.log(elem_det['pos'], ' <<< ********************** <<<')
                    element_details.push(elem_det)
                    i++
            
                }
                return children_size

            }

            function process_elements(parent_element){
                get_child_elements(parent_element.children, 0)
                return element_details
            } 

            function w_override(window, open) {
                window.open = (url) => {
                open.call(window, url, '_self')
                }
			}

            function get_title(){
                title  = document.title;
                return title;
			}

            function get_dom_tree(){ 
                var elements ='';
                var e = document.querySelectorAll('input, div, button, span, label');   
                for (var i=0; i<e.length; i++) {
                    try{
                        elements = elements+" "+e[i].tagName+"("+e[i].getBoundingClientRect().height+");"
                    }
                    catch(err){
                        continue
                    }
                }
                return elements; 
            }

            function get_elements(el, frameIndex){  
                var tags = [];
                var recs = [];   
                var iframe_count = 0 
                width  =Math.max(document.body.scrollWidth, document.body.offsetWidth, document.documentElement.clientWidth, document.documentElement.scrollWidth, document.documentElement.offsetWidth)
                
                if(el==null  ) return recs;
                
               
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
                return recs; 
            }


            function coordSum(rect) {
                return rect.top +
                    rect.right +
                    rect.bottom +
                    rect.left +
                    rect.width +
                    rect.height +
                    rect.x +
                    rect.y;
            }

            function getElementEventsAndCoordinates() {
                const allElements = document.querySelectorAll('*');
                var res = [];
                allElements.forEach(element => {
                    const eventListeners = getEventListeners(element);
                    const eventTypes = Object.keys(eventListeners);
                    if (eventTypes.length !== 0) {
                        events = {}

                        eventTypes.forEach((eventType) => {
                            if (eventType == 'click' || eventType == 'mousedown' || eventType == 'mouseup' || eventType == 'touchstart') {
                                events[eventType] = eventListeners[eventType].reduce((ev, eventListener) => {
                                    ev.push(eventListener.listener.toString());
                                    return ev;
                                }, []);
                            }
                        });
                    }

                    if (Object.keys(events).length > 0) {
                        const rect = element.getBoundingClientRect();
                        if (coordSum(rect) > 0) {
                            res.push({
                                node: element,
                                events: events,
                                rect: rect
                            });
                        }
                    }
                });

                return res;
            }
        """

js_event_scripts =  """


                    function _showEvents(events) {
                        for (let evt of Object.keys(events)) {
                            console.log(evt + " ----------------> " + events[evt].length);
                            for (let i=0; i < events[evt].length; i++) {
                                console.log(events[evt][i].listener.toString());
                            }
                        }
                    };

                    function getAllEventListeners(){
                        wevents = window._getEventListeners();
                        console.log(wevents)
                        _showEvents(wevents);
                    }

                    function get_node_details(el){
                        var element = {}
                        element.innerText  = el.textContent ;        
                        element.tag        = el.tagName!= undefined? el.tagName : '';
                        element.id         = el.id!=null?el.id:'None';
                        element.name       = el.name!=null?el.name:'None';
                        element.type       = el.type ;
                        element.text       = el.Text ;
                        element.value      = el.value ;
                        return element
                    }

                    function log_events_helper(event){
                        console.log(JSON.stringify(get_node_details(event.target)), event.type)
                        event.preventDefault()
                        event.stopPropagation()
                        event.stopImmediatePropagation()
                    }

                    function listAllEventListeners() {

                        const allElements = Array.prototype.slice.call(document.querySelectorAll('*'));
                        allElements.push(document);
                        allElements.push(window);

                        const types = ['onkeypress','onkeydown','onkeyup'];
                        const listener_types = ['keypress','keydown','keyup'];
                        //for (let ev in window) {
                        //    if (/^on/.test(ev)) 
                        //        types[types.length] = ev;
                        //}

                        //console.log(types)
                        let elements = [];
                        for (let i = 0; i < allElements.length; i++) {
                            const currentElement = allElements[i];

                            // Events defined in attributes
                            for (let j = 0; j < types.length; j++) {

                                if (typeof currentElement[types[j]] === 'function') {
                                    
                                    //currentElement.attachEvent(types[j], log_events_helper)

                                    currentElement.addEventListener(types[j].slice(2), log_events_helper) 
                                    elements.push({
                                        "node": get_node_details(currentElement),
                                        "type": types[j]                                    
                                    });
                                }
                            }

                            // Events defined with addEventListener
                            if (typeof currentElement._getEventListeners === 'function') {
                                evts = currentElement._getEventListeners();
                                if (Object.keys(evts).length >0) {
                                    for (let evt of Object.keys(evts)) {         
                                        if (listener_types.includes(evt)){
                                            currentElement.addEventListener(evt, log_events_helper)                      
                                            elements.push({
                                                "node": get_node_details(currentElement),
                                                "type": evt                                    
                                            });      
                                        }                      
                                    }
                                }
                            }
                        }
                        //console.log(elements)
                        return elements;
                    }

                    """

js_add_event_override = """           
                        {
                            EventTarget.prototype._addEventListener = EventTarget.prototype.addEventListener;

                            EventTarget.prototype.addEventListener = function(a, b, c) {
                                    if (c==undefined) c=false;
                                    
                                    this._addEventListener(a,b,c);
                                    if (! this.eventListenerList) this.eventListenerList = {};
                                    if (! this.eventListenerList[a]) this.eventListenerList[a] = [];
                                    this.eventListenerList[a].push({listener:b,options:c});
                            };            
                           
                            

                            EventTarget.prototype._getEventListeners = function(a) {
                                    
                                    if (! this.eventListenerList) this.eventListenerList = {};
                                    if (a==undefined)  { return this.eventListenerList; }
                                    return this.eventListenerList[a];
                            };
                        //alert('hola')
                        }
            """