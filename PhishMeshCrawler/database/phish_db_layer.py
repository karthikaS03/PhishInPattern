from sqlalchemy import *
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from .phish_logger import Phish_Logger
from .phish_db_schema import *
from .phish_db_config import *


logger = Phish_Logger.get_phish_logger('phish_db_layer.py')

db = create_engine(DB_CONN_SERVER)

# db.echo = True

def create_db_session():
  Session = sessionmaker(bind=db, expire_on_commit=False)
  return Session()

def add_site_group_info(site_group_obj):
  try:  
    session = create_db_session()
    site_group =session.query(Site_Groups).filter(text('site_group='+str(site_group_obj.site_group))).first()
    if site_group!=None:
      site_group_obj.site_group_id = site_group.site_group_id  
      session.merge(site_group_obj)
    else:
      session.add(site_group_obj)
    session.commit()
    session.close()
  except Exception as e:
    logger.info('Exception occured in add_site_group_info: '+str(e))

def add_site_images(site_images_obj, group_id):
  try:
    session = create_db_session()
    site_group =session.query(Site_Groups).filter(text('site_group='+str(group_id))).first()
    site_image = session.query(Site_Images).filter(text('site_image_id='+str(site_images_obj.site_image_id))).first()
    if site_group!=None: 
      site_images_obj.site_group_id = site_group.site_group_id
      if site_image!=None:   
        session.merge(site_images_obj)
      else:
        session.add(site_images_obj)  
        session.flush()
    session.commit()
    session.close()
  except Exception as e:
    logger.info('Exception occured in add_site_images: '+str(e))

def check_if_group_exists(group_id):
  try:
    session = create_db_session()
    site_group =session.query(Site_Groups).filter(text('site_group='+str(group_id))).first()
    if site_group!=None: 
      return True
    else:
      return False
    session.commit()
    session.close()
  except Exception as e:
    logger.info('Exception occured in check_if_group_exists: '+str(e))

def get_an_image_per_group():
  try:
    session = create_db_session()
    images  = []
    for site_group in session.query(Site_Groups).all():
      if len(site_group.site_images)>0:
      	images.append({'image_id':site_group.site_images[0].site_image_id, 'group_id': site_group.site_group})
    return images
    session.commit()
    session.close()
  except Exception as e:
    logger.info('Exception occured in get_an_image_per_group: '+str(e))

def add_site_info(site_obj):
  try:
    session = create_db_session()
    site =session.query(Sites).filter(or_(text("phish_tank_ref_id='"+str(site_obj.phish_tank_ref_id+"'")), text("site_url='"+str(site_obj.site_url)+"'"))).first()
    print('query', site)
    if site !=None:
      site_obj.site_id = site.site_id
      # session.merge(site_obj)
    else:  
      if not site_obj.phish_tank_ref_id.isdigit():
        site_obj.phish_tank_ref_id = None
      # site = session.query(Sites).filter(text("site_url='"+str(site_obj.site_url)+"'")).first()
      # if site_obj == None:
      session.add(site_obj )
      session.flush()
      print(site_obj)
    session.commit()
    print('seesion committed')
    return site_obj
    # session.close()
  except Exception as e:
    logger.info('Exception occured in add_site_info: '+str(e))


def add_page_info(page_obj):
  try:
    session = create_db_session()
    session.add(page_obj)
    session.commit()
    # print('seesion committed')
    session.close()
  except Exception as e:
    logger.info('Exception occured in add_page_info: '+str(e))


def add_element_info(elem_obj):
  try:
    session = create_db_session()
    session.add(elem_obj)
    session.commit()
    # print('seesion committed')
    session.close()
  except Exception as e:
    logger.info('Exception occured in add_element_info: '+str(e))

def add_phish_tank_link(phish_tank_link_obj):
  try:
    session = create_db_session()
    link =session.query(Phish_Tank_Links).filter(text('phish_tank_ref_id='+str(phish_tank_link_obj.phish_tank_ref_id))).first()
    if link !=None:
      session.merge(phish_tank_link_obj)
    else:
      session.add(phish_tank_link_obj)
    session.commit()
    session.close()
  except Exception as e:
    logger.info('Exception occured in add_phish_tank_link: '+str(e))

def add_domain_info(domain_obj):
  try:
    session = create_db_session()
    domain =session.query(Domains).filter(text('domain_name="'+domain_obj.domain_name+'"')).first()
    if domain !=None:
      id = domain.domain_id   
      session.commit()
      session.close()
      return id
    else:
      session.add(domain_obj)
      session.commit()    
      
      id = domain_obj.domain_id   
      session.close()  
      return id
  except Exception as e:
    logger.info('Exception occured in add_domain_info: '+str(e))

def check_if_link_exists(phish_id):
  try:
    session = create_db_session()
    link =session.query(Phish_Tank_Links).filter(text('phish_tank_ref_id='+str(phish_id))).first()
    session.commit()
    session.close()
    return link
  except Exception as e:
    logger.info('Exception occured in check_if_link_exists: '+str(e))

def add_page_details(page_obj, phish_tank_ref_id):
  try:
    session = create_db_session()
    site = session.query(Sites).filter(text('phish_tank_ref_id='+str(phish_tank_ref_id))).first()
    if site !=None:
      page_obj.site_id = site.site_id
      session.add(page_obj)
      session.flush()
      print('page_added::', page_obj.page_id)
      print(page_obj.elements)
      for elem in page_obj.elements:
        elem.page_id = page_obj.page_id
        # add_element_info(elem)
      return page_obj.page_id
    session.commit()
    session.close()
  except Exception as e:
    logger.info('Exception occured in add_page_details: '+str(e))

def find_category_id(category_name):
  try:
    session = create_db_session()
    category =session.query(Field_Category).filter(text('field_category_name="'+category_name+'"')).first()
    if category !=None:
      id = category.field_category_id
      session.commit()
      session.close()
      return id 
    return -99
  except Exception as e:
    logger.info('Exception occured in find_category_id: '+str(e))

def add_pages_to_site(phish_tank_ref_id, site_pages, surl):
  # print(site_pages)
  try:
    session = create_db_session()
    site = session.query(Sites).filter(text('phish_tank_ref_id='+str(phish_tank_ref_id))).first()
    if site == None:
      site = session.query(Sites).filter(text("site_url='"+str(surl)+"'")).first()
      if site == None:
        site = Sites(site_url = surl)
        session.add(site)
        session.flush()
        # session.commit()
    
    for page in site_pages:
      p = session.query(Pages).filter(text('page_image_id="'+str(page.page_image_id)+'"')).first()
      print('Page queried', p)
      if p==None:
        print('Appending page to site')
        site.pages.append(page)
        # add_page_details(page,phish_tank_ref_id)
    session.merge(site)
    # print(site)
    session.commit()
    session.close()
  except Exception as e:
    logger.info('Exception occured in add_pages_to_site: '+str(e))

def fetch_field_training_set():
  try:
    session = create_db_session()
    training_set = []
    for s in session.query(Field_Training_Set).all():
      a={}
      a['text'] =  s.field_text
      a['category'] = s.tbl_FieldCategory.field_category_name
      training_set.append(a)
    session.commit()
    session.close()
    return training_set
  except Exception as e:
    logger.info('Exception occured in fetch_field_training_set: '+str(e))

def fetch_phishtank_urls(count=100):
  try:
    session = create_db_session()
    phish_urls = []
    for s in session.query(Phish_Tank_Links).filter(and_(Phish_Tank_Links.is_analyzed==None,Phish_Tank_Links.status=='Online')).limit(count).all():
      a = Phish_Tank_Links(phish_tank_ref_id = s.phish_tank_ref_id, phish_tank_url = s.phish_tank_url)
      # print(a)
      phish_urls.append(a)
    session.commit()
    session.close()
    return phish_urls
  except Exception as e:
    print(e)
    logger.info('Exception occured in fetch_field_training_set: '+str(e))

def get_site_id(phish_id):
  try:
    session = create_db_session()
    site_id = session.query(Site).filter(phish_tank_ref_id==phish_id).first()
    if site_id[0] ==None:
      session.commit()
      return 0
    else:
      session.commit()
      session.close()
      return site_id[0]
  except Exception as e:
    logger.info('Exception occured in get_site_id: '+str(e))

def get_max_site_id():
  try:
    session = create_db_session()
    max_id = session.query(func.max(Site_Images.site_image_id)).first()
    if max_id[0] ==None:
      session.commit()
      return 0
    else:
      session.commit()
      session.close()
      return max_id[0]
  except Exception as e:
    logger.info('Exception occured in get_max_site_id: '+str(e))

def fetch_unclassified_elements():
  try:
    session = create_db_session()
    elements = []
    for s in session.query(Elements).filter_by(field_category_id=-99):
      element={}
      element['html_id'] =  s.element_html_id
      element['name'] = s.element_name
      element['text'] = s.element_parsed_text
      element['id'] = s.element_id
      elements.append(element)
    session.commit()
    session.close()
    return elements
  except Exception as e:
    logger.info('Exception occured in fetch_unclassified_elements: '+str(e))
    
    

def update_element(element):
  try:
    session = create_db_session()
    e = session.query(Elements).get(element.element_id)
    e.element_id=element.element_id
    e.element_value = element.element_value
    e.field_category_id = element.field_category_id
    e.element_parsed_method = element.element_parsed_method
    session.commit()
    session.close()
  except Exception as e:
    logger.info('Exception occured in update_element: '+str(e))


def update_analysis_url(phishtank_obj):
  try:
    session = create_db_session()
    e = session.query(Phish_Tank_Links).get(phishtank_obj.phish_tank_ref_id)
    e.is_analyzed = phishtank_obj.is_analyzed
    session.commit()
    session.close()
  except Exception as e:
    logger.info('Exception occured in update_element: '+str(e))
    
def add_site_status(site_status):
  try:
    session = create_db_session()
    session.add(site_status)
    session.commit()
    session.close()
  except Exception as e:
    logger.info('Exception occured in add_site_status: '+str(e))

def add_page_status(page_status):
  try:
    session = create_db_session()
    session.add(page_status)
    session.commit()
    session.close()
  except Exception as e:
    logger.info('Exception occured in add_page_status: '+str(e))

def add_domain_certificate(domain_certificate):
  try:
    session = create_db_session()
    session.add(domain_certificate)
    session.commit()
    session.close()
  except Exception as e:
    logger.info('Exception occured in add_page_status: '+str(e))

def add_domain_certificate_status(domain_certificate_status):
  try:
    session = create_db_session()
    session.add(domain_certificate_status)
    session.commit()
    session.close()
  except Exception as e:
    logger.info('Exception occured in add_page_status: '+str(e))
    
    
def add_host_info(host_info):
  try:
    session = create_db_session()
    session.add(host_info)
    session.commit()
    session.close()
  except Exception as e:
    logger.info('Exception occured in add_host_info: '+str(e))

def add_page_req_info(req_info):
  try:
    session = create_db_session()
    session.add(req_info)
    session.commit()
    session.close()
  except Exception as e:
    logger.info('Exception occured in add_page_req_info: '+str(e))

def add_page_rsp_info(rsp_info):
  try:
    session = create_db_session()
    session.add(rsp_info)
    session.commit()
    session.close()
  except Exception as e:
    logger.info('Exception occured in add_page_rsp_info: '+str(e))

def get_phish_ids():
  try:
    session = create_db_session()
    pages = []
    phish_ids = session.query(Phish_Tank_Links.phish_tank_ref_id).all()
    session.commit()
    session.close()
    
    return phish_ids
  except Exception as e:
    logger.info('Exception occured in get_phish_ids(): '+str(e))
    
def get_categories():
  try:
    session = create_db_session()
    categories = session.query(Field_Category.field_category_name).all()
    session.commit()
    session.close()
    
    return categories
  except Exception as e:
    logger.info('Exception occured in get_categories: '+str(e))    

def fetch_pages_for_download():
  try:
    session = create_db_session()
    pages = []
    subquery = session.query(Page_Status.page_id)
    for p in session.query(Pages).filter(~Pages.page_id.in_(subquery)):
      page={}
      page['page_id'] =  p.page_id
      page['page_url'] = p.page_url
      page['page_image_id'] = p.page_image_id
      pages.append(page)
    session.commit()
    session.close()
    return pages
  except Exception as e:
    logger.info('Exception occured in fetch_pages_for_download(): '+str(e))

def fetch_domains_for_certificate():
  try:
    session = create_db_session()
    domains = []
    subquery = session.query(Domain_Certificate_Status.domain_id)
    for s in session.query(Sites).filter(~Sites.domain_id.in_(subquery)).filter(Sites.site_url.like("%https%")):
      domain={}
      domain['domain_id'] =  s.domain_id
      domain['domain_name'] = s.domains.domain_name
      domains.append(domain)
    session.commit()
    session.close()
    return domains
  except Exception as e:
    logger.info('Exception occured in fetch_domains_for_certificate(): '+str(e))
    
def fetch_domains_for_host_details():
  try:
    session = create_db_session()
    domains = []
    subquery = session.query(Domain_Host_Info.domain_id)
    for d in session.query(Domains).filter(~Domains.domain_id.in_(subquery)):
      domain={}
      domain['domain_id'] =  d.domain_id
      domain['domain_name'] = d.domain_name
      domains.append(domain)
    session.commit()
    session.close()
    return domains
  except Exception as e:
    logger.info('Exception occured in fetch_domains_for_host_details(): '+str(e))