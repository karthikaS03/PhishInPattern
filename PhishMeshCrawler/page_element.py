import json
import operator
from phish_logger import Phish_Logger

logger = Phish_Logger.get_phish_logger('page_element.py')

class Page_Element(object):
    
	# The class "constructor" - It's actually an initializer 
	def __init__(self, name, tag, html_id):
		self.name = name
		self.tag = tag
		self.html_id = html_id
		self.form =''
		self.frameIndex = -1
		self.element_id = 0
		self.parsed_texts=[]
		self.parsed_methods=[]
		self.categories=[]
		self.values=[]
		self.scores= []

	def __repr__(self):
    		return 'Element Id %d:  Name: "%s  Html_Id: %s ' % (self.element_id, self.name, self.html_id)

	
	def get_category_value(self):
		try:
			logger.info("get_category_value(): Count:" +str(len(self.categories)))
			categories_count = { c: self.categories.count(c) for c in set(self.categories) if c!='unknown' and c!=""}
			categories_count = sorted(categories_count, key= operator.itemgetter(1), reverse=True)
			# print('soted categories', categories_count)
			for category,value,pt,pm in zip(self.categories,self.values, self.parsed_texts,self.parsed_methods):
				logger.info("get_category_value(): Category: "+category+"; Value :"+str(value)+"; Parsed Text: "+pt+"; Parsed Method :"+pm)
				if len(categories_count)>0 and category in categories_count[0] and len(category)>0 and category!='unknown' and (value!=None or value!='None'):
					logger.info("get_category_value(): Valid  Category: "+category+"; Value :"+value+"; Parsed Text: "+pt+"; Parsed Method :"+pm)
					return (category,value,pt,pm)
			logger.info("get_category_value(): No Match")
		except Exception as e:
			logger.info("get_category_value(): Exception Occured!! "+ str(e))
		return ('unknown', 'default',self.parsed_texts.pop() if self.parsed_texts else 'None', ';'.join(self.parsed_methods) if self.parsed_methods else 'None')