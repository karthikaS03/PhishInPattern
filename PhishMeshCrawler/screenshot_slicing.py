#!/usr/bin/python
# coding=utf8

from PIL import Image, ImageDraw
import pytesseract
from PIL import Image, ImageEnhance, ImageFilter
from autocorrect import spell
# import re, HTMLParser, urllib2
from phish_logger import Phish_Logger

logger = Phish_Logger.get_phish_logger('Screenshot_slicing.py')

def remove_file_extension(file_name):
	tokens = file_name.split('.')
	if (len(tokens) <= 1):
		return file_name

	s = '.'.join(tokens[0:len(tokens)-1])
	return s

def img_to_text(image_file,typ, x1, y1, x2, y2, zoom_factor=2):
	try:   
		im = Image.open(image_file) 
		(sw,sh) = im.size
		im = im.resize((sw*1,sh*1),Image.ANTIALIAS)
		im.save(image_file)
		draw = ImageDraw.Draw(im)
		draw.rectangle(((x1,y1),(x2,y2)), outline = "red")
		img = img_slice_and_zoom(image_file,typ, x1, y1, x2, y2,zoom_factor)
		text = img_ocr(img)
		#print('screenshot:', text)
		if '/' in text:
			text = text.replace('/','-')
		img_slice = Image.open(img)
		img_name = remove_file_extension(img)
		img_ext = img_slice.format.lower()
		text = text.encode('ascii','ignore').decode() #text.decode('unicode_escape').encode('ascii','ignore')
		ocr_slice_file = img_name+'-'+text+'.'+img_ext
		img_slice.save(ocr_slice_file)
		#text = spell_check(text.decode('unicode_escape').encode('ascii','ignore')+" autocorect")
		#return text[0:text.index("auto")];
		return text
	except Exception as e:
		logger.info('img_to_text(%s,%s,%f,%f,%f,%f,%f): Exception -> %s'  % (image_file,typ, x1, y1, x2, y2, zoom_factor,str(e)))
	return ""
	'''
	  for i in range(1,2):
	    if len(text) <=1:
	      if typ=='L':
	        x1 = x1 - 30
	        x2 = x2 - 30
	        img = img_slice_and_zoom(image_file,typ, x1, y1, x2, y2,zoom_factor)
	        text = img_ocr(img) 
	        text = spell_check(text)
	      elif typ=='T':
	        y1 = y1-10
	        y2 = y2-10
	        img = img_slice_and_zoom(image_file,typ, x1, y1, x2, y2,zoom_factor)
	        text = img_ocr(img)
	        text = spell_check(text)
	    else:
	      return text;
	  return " ";
	'''

def img_slice_and_zoom(image_file,typ, x1, y1, x2, y2, zoom_factor=2):
	try:
		img = Image.open(image_file)
		img_name = remove_file_extension(image_file)
		img_ext = img.format.lower()
		logger.info('img_slice_and_zoom(%s,%s,%f,%f,%f,%f,%f): Started '  % (image_file,typ, x1, y1, x2, y2, zoom_factor))
		# make sure image boundaries are respected
		x1 = max(0,x1)
		y1 = max(0,y1)
		x2 = min(x2,img.size[0]) if  img.size[0]>=0 else x2 
		x2 = x2 if x2>=0 and x2!=x1 else x1+100
		y2 = min(y2,img.size[1]) if  img.size[1]>=0 else y2 
		y2 = y2 if y2>=0 and y2!=y1 else y1+20

		s = img.crop((x1,y1,x2,y2))
		slice_info = "slice:_%s--%s-%s-%s-%s" % (str(typ),x1,y1,x2,y2)
		slice_file = img_name+'-'+slice_info+'.'+img_ext

		szoom = s
		szoom_file = slice_file
		if (zoom_factor > 0) : 
			(sw,sh) = s.size
			szoom = s.resize((sw*zoom_factor,sh*zoom_factor),Image.ANTIALIAS)
			szoom_file = img_name+'-'+slice_info+'-x'+str(zoom_factor)+'_zoom'+'.'+img_ext
		szoom.save(szoom_file)
		return szoom_file
	except Exception as e:
		logger.info('img_slice_and_zoom(%s,%s,%f,%f,%f,%f,%f): Exception -> %s'  % (image_file,typ, x1, y1, x2, y2, zoom_factor,str(e)))
	return image_file
  


def img_ocr(image_file):  
	text=""  
	try:
		im = Image.open(image_file)
		im = im.filter(ImageFilter.MedianFilter())
		enhancer = ImageEnhance.Contrast(im)
		im = enhancer.enhance(1)
		#im = im.convert('1')
		text=''
		text = pytesseract.image_to_string(im)
		#print('img2ocr ::', text)
		im.save(image_file)
		return text
	except Exception as e:
		logger.info('img_ocr(%s,%s): Exception -> %s'  % (image_file,text,str(e)))

# def spell_check(text):
# 	gs = GoogleSearch(text)
# 	html = gs._get_results_page()
# 	html_parser = HTMLParser.HTMLParser()
# 	match = re.search(r'(?:Showing results for)[^\0]*?<a.*?>(.*?)</a>', str(html))
# 	fix=''
# 	if match is None:
# 		return text
# 	else:
# 		fix = match.group(1)
# 		fix = re.sub(r'<.*?>', '', fix)    
# 		fix = html_parser.unescape(fix)
# 	return fix
