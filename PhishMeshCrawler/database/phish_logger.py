import logging
import os
import datetime
currentdir = os.path.dirname(os.path.realpath(__file__))

class Phish_Logger:
	@staticmethod
	def get_phish_logger(name):
		logger = logging.getLogger(name)
		logger.setLevel(logging.INFO)
		dir_path = os.path.abspath(os.path.dirname(__file__))
		handler = logging.FileHandler(os.path.join(currentdir+'/../../data/db_logs/','phish_logger_'+str(datetime.datetime.now().date())+'.log'))
		handler.setLevel(logging.INFO)

		# create a logging format
		formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
		handler.setFormatter(formatter)

		# add the handlers to the logger
		if not logger.handlers:
			logger.addHandler(handler)
		return logger


