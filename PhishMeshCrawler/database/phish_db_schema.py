from sqlalchemy import *
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
import json
import datetime


if __name__ == '__main__':

  import phish_db_config
  DB_CONN_SERVER = phish_db_config.DB_CONN_SERVER

  db = create_engine(DB_CONN_SERVER)
  db.echo = True


  metadata = MetaData(db)
  base = declarative_base()

  Session = sessionmaker(bind=db)

  session =Session()
  base.metadata.create_all(db)
  session.flush()
  session.commit()

  session =Session()
  train={}
  '''
  with open('TrainingSet.json','r') as f:
    train =json.load(f)
  for obj in train:
    category = Field_Category(field_category_name = obj['category'])
    for text in obj['texts']:
      category.training_set.append(Field_Training_Set(field_text = text))
    session.add(category) 
  '''

  session.flush()
  session.commit()
else:
  from .phish_db_config import *
    
  db = create_engine(DB_CONN_SERVER)
  db.echo = True


  metadata = MetaData(db)
  base = declarative_base()

class Field_Category(base):
  __tablename__ ='tbl_FieldCategory'
  field_category_id = Column(Integer, primary_key = True)
  field_category_name = Column(String(30))
  elements = relationship("Elements", backref='tbl_FieldCategory')
  training_set = relationship("Field_Training_Set", backref='tbl_FieldCategory')
  def __repr__(self):
    return 'Category %d: "%s"' % (self.field_category_id, self.field_category_name)
 
class Field_Training_Set(base):
  __tablename__ ='tbl_FieldCategoryTrainingData'
  data_id = Column(Integer, primary_key = True)
  field_category_id = Column(Integer,  ForeignKey('tbl_FieldCategory.field_category_id') )
  field_text =Column(String(100))
  def __repr__(self):
    return 'Category %d: "%s" "%s"' % (self.data_id, self.field_text,self.tbl_FieldCategory.field_category_name)

class Target_Sites(base):
  __tablename__ ='tbl_TargetSites'
  target_site_id = Column(Integer, primary_key = True)
  target_site_name = Column(String(100))
  # sites = relationship("Sites", backref='tbl_TargetSites')
  def __repr__(self):
    return 'Target Site  %d: "%s"' % (self.target_site_id, self.target_site_name)

class Site_Groups(base):
  __tablename__ ='tbl_SiteGroups'
  site_group_id = Column(Integer, primary_key = True)
  site_group = Column(Integer)
  site_images = relationship("Site_Images", backref='tbl_Site_Groups')
  def __repr__(self):
    return 'Site Group  %d: %d' % (self.site_group_id, self.site_group)

class Domains(base):
  __tablename__ ='tbl_Domains'
  domain_id = Column(Integer, primary_key = True)
  domain_name = Column(String(200))
  trust_score = Column(Integer)
  sites = relationship("Sites", backref='domains')
  def __repr__(self):
    return 'Domain  %d: "%s" %d' % (self.domain_id, self.domain_name, self.trust_score)

class Phish_Tank_Links(base):
  __tablename__ ='tbl_PhishTankLinks'
  phish_tank_ref_id = Column(Integer, primary_key = True)
  phish_tank_url = Column(String(300))
  recorded_datetime = Column(DateTime)
  verification_datetime = Column(DateTime)
  target = Column(String(100))
  status = Column(String(100))
  is_analyzed= Column(Boolean)
  sites = relationship("Sites", backref='tbl_PhishTankLinks')
  def __repr__(self):
    return 'Phishtank Links  %d: "%s" %s' % (self.phish_tank_ref_id, self.phish_tank_url,self.status)

class Site_Images(base):
  __tablename__ ='tbl_SiteImages'
  site_image_id = Column(Integer, primary_key = True)
  site_group_id = Column(Integer,  ForeignKey('tbl_SiteGroups.site_group_id'))
  site_similar_to = Column(Integer)
  # sites = relationship("Sites", backref='tbl_Site_Images')
  def __repr__(self):
    return 'Site Images  %d: %d %d' % (self.site_image_id, self.site_group_id, self.site_similar_to)

class Sites(base):
  __tablename__ ='tbl_Sites'
  site_id = Column(Integer, primary_key = True)
  site_url = Column(String(300))
  phish_tank_ref_id = Column(Integer, ForeignKey('tbl_PhishTankLinks.phish_tank_ref_id'))
  # site_image_id = Column(Integer, ForeignKey('tbl_SiteImages.site_image_id'))
  domain_id = Column(Integer, ForeignKey('tbl_Domains.domain_id'))
  # target_site_id = Column(Integer, ForeignKey('tbl_TargetSites.target_site_id'))
  pages = relationship("Pages", backref='tbl_Sites')
  def __repr__(self):
    return 'Sites  %s: "%s" %s' % (self.site_id, self.site_url, self.phish_tank_ref_id)

class Pages(base):
  __tablename__ ='tbl_Pages'
  page_id = Column(Integer, primary_key = True)
  page_url = Column(String(300)) 
  page_title=Column(String(100))
  site_id = Column(Integer, ForeignKey('tbl_Sites.site_id'))
  page_image_id = Column(String(50))
  elements = relationship("Elements", backref='tbl_Pages')
  requests = relationship("Page_Request_Info", backref='tbl_PageRequestInfo')
  responses = relationship("Page_Response_Info", backref='tbl_PageResponseInfo')
  def __repr__(self):
    return 'Pages  "%s" %d' % ( self.page_url, self.site_id)

class Elements(base):
  __tablename__ ='tbl_Elements'
  element_id = Column(Integer, primary_key = True)
  element_name = Column(String(50))
  element_tag = Column(String(50))
  element_html_id = Column(String(50))
  element_parsed_text = Column(String(100))
  element_form = Column(String(50))
  element_value = Column(String(100))
  element_position = Column(String(50))
  element_parsed_method = Column(String(100))
  page_id = Column(Integer, ForeignKey('tbl_Pages.page_id')) 
  field_category_id = Column(Integer, ForeignKey('tbl_FieldCategory.field_category_id'))
  element_frame_index = Column(Integer)
  def __repr__(self):
    return 'Elements  : "%s" "%s" "%s" "%s" "%s" %d' % (self.element_tag, self.element_name, self.element_html_id, self.element_parsed_text, self.element_value,  self.field_category_id)

class Site_Status(base):
  __tablename__ ='tbl_SiteStatus'
  status_id = Column(Integer, primary_key = True)
  status = Column(String(100)) 
  phish_id = Column(Integer, ForeignKey('tbl_PhishTankLinks.phish_tank_ref_id'))
  def __repr__(self):
    return 'Site Status  %d: "%s" %d' % (self.status_id, self.status, self.phish_id)

class Page_Status(base):
  __tablename__ ='tbl_PageStatus'
  page_status_id = Column(Integer, primary_key = True)
  download_date = Column(Date, default=datetime.datetime.now().date())
  download_status = Column(String(100))
  page_id = Column(Integer, ForeignKey('tbl_Pages.page_id')) 
  def __repr__(self):
    return 'Page Status  %d: "%s" %d' % (self.page_status_id, str(self.download_time), self.page_id)

class Domain_Certificates(base):
  __tablename__ ='tbl_DomainCertificates'
  certificate_id = Column(Integer, primary_key = True)
  valid_after = Column(DateTime) 
  valid_before = Column(DateTime)
  is_ca = Column(Integer)
  subject=Column(String(500))
  issuer=Column(String(500))
  subject_alt_names = Column(String(5000))
  domain_id = Column(Integer, ForeignKey('tbl_Domains.domain_id'))
  is_valid = Column(Integer)
  comments = Column(String(500))
  def __repr__(self):
    return 'Certificates  %d: %s %s %d %s' % (self.certificate_id, self.valid_after, self.valid_before, self.is_ca, self.subject)
    
class Domain_Certificate_Status(base):
  __tablename__ ='tbl_DomainCertificatesValidity'
  certificate_status_id = Column(Integer, primary_key = True)
  domain_id = Column(Integer, ForeignKey('tbl_Domains.domain_id'))
  is_valid = Column(Integer)
  comments = Column(String(500))
  def __repr__(self):
    return 'Certificates  %d: %s' % (self.certificate_status_id, self.comments)
    
class Domain_Host_Info(base):
  __tablename__ ='tbl_DomainHostInfo'
  host_id = Column(Integer, primary_key = True)
  domain_id = Column(Integer, ForeignKey('tbl_Domains.domain_id'))
  geo_loc_details = Column(String(3000))
  registered_domain = Column(String(500))
  detected_by_blacklists = Column(String(5000))
  blacklisted_count = Column(Integer)
  total_blacklists =Column(Integer)
  ip_addr=Column(String(20))
  def __repr__(self):
    return 'Domain_Host_Details  %d: %s' % (self.host_id, self.detected_by_blacklists)
    

class Page_Request_Info(base):
  __tablename__ = 'tbl_PageRequestInfo'
  request_id = Column(Integer, primary_key = True)
  request_url = Column(String(3000))
  request_domain = Column(String(100))
  request_method = Column(String(10))
  request_type = Column(String(15))
  page_id = Column(Integer, ForeignKey('tbl_Pages.page_id'))
  def __repr__(self):
    return 'Page_Request_Info %d : %s' %(self.request_id, self.request_url)



class Page_Response_Info(base):
  __tablename__ = 'tbl_PageResponseInfo'
  response_id = Column(Integer, primary_key = True)
  response_url = Column(String(3000))
  response_file_path = Column(String(500))
  response_file_hash = Column(String(50))
  page_id = Column(Integer, ForeignKey('tbl_Pages.page_id'))
  def __repr__(self):
    return 'Page_Response_Info %d : %s' %(self.response_id, self.response_url)

