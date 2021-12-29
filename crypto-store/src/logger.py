#!/usr/bin/env python3

import json
import time as time_
from datetime import datetime
from os import path
from hashlib import sha256

from email.message import EmailMessage

try:
	from const import REPO_PATH
except:
	# assume in current working dir. 
	REPO_PATH = '.'


# following class is really just a way to organize methods. all are static.
# this is mainly used for keeping json records on orders through the store. 
# set the JSON_ORDER_PATH and TEXT_TX_REC_PATH as needed (second is more for testing purposes)
class Logger(object):
	JSON_ORDER_PATH = path.join(REPO_PATH, "data", "json_order_data")
	TEXT_TX_REC_PATH = path.join(REPO_PATH, "data", "tx_records")

	def __init__(self):
		pass

	# this logging is more for test purposes
	@staticmethod
	def log_txt_file(tx_code: str, text: str, newlines=1):
		# text should be str (or castable) and newlines should be greater than 1.
		try:
			text = str(text)
		except:
			raise ValueError(f"parameter must be castable to str, not type {type(text)} (text was {text})")
		
		if not isinstance(newlines, int):
			newlines = 1
		else:
			newlines = max(newlines, 1) # should be positive.
		
		line = ('\n' * (newlines-1)) + text + f" ({str(datetime.now())})"
		print(line)
		line = '\n' + line # this whole thing is because printing naturally adds a newline while appending does not.
		with open(Logger.gen_tx_rec_path(tx_code), 'a') as f:
			f.write(line)
		
		return line # might as well. 
	

	# this tries to read a json and return the dict, given an order_num
	# returns empty dict if not found
	@staticmethod
	def read_json(order_num: str):
		full_path = Logger.gen_json_path(order_num)
		if not(path.exists(full_path)):
			return {} # nothing there.
		
		with open(full_path, 'r') as f:
			return json.loads(''.join(f.readlines()))


	# this writes to a json file. It will only add data (or overwrite it) but never deletes any.
	@staticmethod
	def write_json(order_num: str, data: dict):
		full_path = Logger.gen_json_path(order_num)
		data_on_rec = Logger.read_json(order_num)
		if len(data_on_rec) == 0:
			# nothing there. just write it all
			with open(full_path, 'w') as f:
				f.write(json.dumps(data))
			return

		# we never want to throw away any data. 
		for key, val in data_on_rec.items():
			if not(key in data):
				# assign old val.
				data[key] = val

		# ready to write.
		with open(full_path, 'w') as f:
			f.write(json.dumps(data))
	
	
	@staticmethod
	def gen_json_path(order_num: str):
		return path.join(Logger.JSON_ORDER_PATH, f"order_num_{order_num}.json")


	@staticmethod
	def gen_tx_rec_path(tx_code: str):
		return path.join(Logger.TEXT_TX_REC_PATH, f"tx_rec_{tx_code}.txt")

	# these tx_codes are used for internal organization and as idempotency keys inside of the zinc api (zinc.py)
	@staticmethod
	def gen_tx_code():
		full_hash = sha256(str(time_.time()).encode()).hexdigest()
		tx_code = full_hash[0:16]
		#TODO: check to see if collisions avoided. (they pare not likely.)
		return tx_code