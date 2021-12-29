#!/usr/bin/env python3

import json
import requests
from datetime import datetime, timedelta
from requests.auth import HTTPBasicAuth

from const import ZINC_MAX_COST
from logger import Logger
from secrets import CredsManager


#NOTE (global)
# it seems that for items with multiple types/variants, just click on the type (on amazon) and use that URL. the code will be slightly different.

ZINC_TOKEN = CredsManager.get_zinc_creds()["api_secret"]
ZINC_API_LINK = "https://api.zinc.io/v1"

# following takes address dict and cleans it and returns it. it returns None if critical info is missing. 
def _clean_address(address: dict):
	if not "address_line2" in address:
		address["address_line2"] = ""
	
	REQS = ["first_name", "last_name", "address_line1", "address_line2", "zip_code", "city", "state", "country", "phone_number"]
	for req in REQS:
		if not req in address:
			return None

	temp = address
	address = {}
	for req in REQS:
		address[req] = temp[req]
	
	return address


# we are going to do basic authentification.
# pretty sure that the zinc token is the 'user' and the password is ' ' (or maybe '')
def get_auth(token: str):
	# take in as parameter so can test with explicitly wrong ones. 
	return HTTPBasicAuth(token, ' ')

def to_epoch_mill(dt_str, dt_form="%m-%d-%Y"):
	dt = datetime.strptime(dt_str, dt_form)
	epoch_mill = 1_000 * dt.timestamp()
	return round(epoch_mill)

# the following method raises an Exception when more than one product code is found
def get_amzn_prod_code(url: str):
	# there is some variation, so let's just be careful...
	if not isinstance(url, str):
		raise ValueError("url must be a str.")

	url = url.replace("?", "/")
	url = url.replace("&", "/")
	url_els = url.split("/")
	codes = [] # list in case we find more than one, in which case we raise an exception

	for el in url_els:
		el = ''.join(el.split()) # just to be safe. 
		if len(el) == 10:
			# want to check that it is all alpha numeric
			valid = True
			for char in el:
				if not(char.isupper() or char.isdigit()):
					valid = False
					break
			
			if valid:
				codes.append(el)

	if len(codes) == 0:
		raise Exception(f"Could not find a product code in url {url}.")
	
	if len(codes) > 1:
		raise Exception(f"Found multiple codes ({codes}) in url {url}.")
	
	return codes[0]

def get_all_orders(token: str, retailer="amazon"):
	# pretty rough, going to set limit high as well as starting from and ending from. 
	order_url = ZINC_API_LINK + "/orders"
	lim = 10_000
	# starting date just choose one from a while ago. 
	start = to_epoch_mill("05-15-2010")
	# ending a little more complicated. want to get a datestring formatted as above for a few days from NOW
	end_dt = datetime.now() + timedelta(days=5)
	end = to_epoch_mill(end_dt.strftime("%m-%d-%Y"))

	# now construct the params
	params = {"limit": lim, "starting_after": start, "ending_before": end, "retailer": retailer}
	r = requests.get(order_url, params=params, auth=get_auth(token))
	return r.json()

def place_sing_amzn_order(token: str, tx_code: str, address: dict, prod_code: str, max_cost=1):
	# default to lowest max_cost to avoid accidental orders. 
	# address should be a dict with a few parameters. below is one example: 
			# "first_name": "Tim",
			# "last_name": "Beaver",
			# "address_line1": "77 Massachusetts Avenue",
			# "address_line2": "",
			# "zip_code": "02139",
			# "city": "Cambridge",
			# "state": "MA",
			# "country": "US",
			# "phone_number": "5551230101"

	# now check for these params (and that it is a dict).
	if not isinstance(address, dict):
		raise ValueError("param address must be a dict.")
	
	# first exception is if address_line2 is not present, just make it blank
	if not "address_line2" in address:
		address["address_line2"] = ""
	
	REQS = ["first_name", "last_name", "address_line1", "address_line2", "zip_code", "city", "state", "country", "phone_number"]
	
	for req in REQS:
		if not req in address:
			raise KeyError(f"param address must contain key {req}. All required are: {str(REQS)}")

	# if here, address is valid. 
	# check prod code for good practice. 
	if not isinstance(prod_code, str) or (len(prod_code) != 10):
		raise ValueError(f"parameter prod_code must be a 10 length str of capitals and digits, was {prod_code}")
	
	valid = True
	for char in prod_code:
		if not(char.isupper() or char.isdigit()):
			valid = False
	
	if not valid:
		raise ValueError(f"parameter prod_code must be a 10 length str of capitals and digits, was {prod_code}")

	if not isinstance(max_cost, int) or max_cost <= 0 or max_cost > ZINC_MAX_COST:
		raise ValueError(f"parameter max_cost must be an int between 1 and ZINC_MAX_COST={ZINC_MAX_COST} (inclusive). Was {max_cost}")
	
	# next, want to clean up address. i.e. eliminate any non-necc parameters. 
	temp = address
	address = {}
	for key, val in temp.items():
		if key in REQS:
			address[key] = val

	# now are ready to start going...
	payload = {}
	payload["retailer"] = "amazon"
	payload["products"] = [{"product_id": prod_code, "quantity": 1}]
	payload["max_price"] = max_cost
	payload["shipping_address"] = address
	payload["shipping_method"] = "cheapest" # NOTE: maybe change? maybe not...
	payload["addax"] = True
	payload["idempotency_key"] = tx_code # this is to avoid duplicate orders. 
	payload["client_notes"] = {"internal_tx_code": tx_code}

	order_url = ZINC_API_LINK + "/orders"

	r = requests.post(order_url, auth=get_auth(token), data=json.dumps(payload))
	if r.status_code < 200 or r.status_code > 299:
		raise Exception(f"Got status code {r.status_code}. Content was {r.content}")
	
	con = r.json()
	if not("request_id" in con):
		raise Exception(f"Did not find a request_id, content was {r.content}")
	
	# otherwise all good to return the id for later use
	req_id = con["request_id"]
	print(f"Order placed with request_id: {req_id}")
	print(r.content)
	return req_id

# following assumes to some extent that the product code is valid. best to make a check near the beginning. 
#TODO refactor prod code checking to be more efficient. not critical 
# the following method returns a dict that has lots of useful info. in particular, the name/title and price. 
def get_prod_data(token: str, prod_code: str, retailer="amazon"):
	prod_url = ZINC_API_LINK + "/products/" + prod_code
	params = {"retailer": retailer}
	r = requests.get(prod_url, params=params, auth=get_auth(token))
	if r.status_code < 200 or r.status_code > 299:
		raise Exception(f"status code in get_prod_data was {r.status_code}. request content was {r.content}.")
	
	return r.json()


# following returns a tuple. first is a bool. true for completed, false for otherwise. second is the actual response data. 
# raises an exception if the actual request fails (which should not really happen much...)
def get_order_status(token: str, req_id: str):
	order_url = ZINC_API_LINK + "/orders/" + req_id
	r = requests.get(order_url, auth=get_auth(token))
	if r.status_code < 200 or r.status_code > 299:
		raise Exception(f"request failed. status code was {r.status_code}. content was {r.content}.")
	
	# otherwise we are good to check. 
	con_json = r.json()
	if ("_type" in con_json) and (con_json["_type"] == "order_response"):
		return (True, con_json) # this indicates a successful order.
	else:
		return (False, con_json) # this indicates a non-successful order. 

# returns dict of req_ids to objects. either tuples (bool, content) -- true for completed purchase, false for error (not done, etc). or None -- indicates order not found in system. 
def get_order_statuses(token: str, req_ids: list, retailer="amazon", limit=10_000, starting_after=None, ending_before=None, skip=None):
	#TODO: add support for the starting after, ending before, skip stuff
	# do basic type verification.
	try:
		limit = int(limit)
		limit = max(limit, 1) # positive.
	except:
		limit = 10_000
	
	if not((starting_after is None) and (ending_before is None) and (skip is None)):
		raise NotImplementedError("have not implemented starting_after, ending_before, skip for this method.")
	
	try:
		req_ids = [r_id.lower().strip() for r_id in req_ids]
	except Exception as e:
		raise ValueError(f"param req_ids must be a list of strings. could not make lower and strip. raised \"{str(e)}\"")
	
	order_url = ZINC_API_LINK + "/orders"
	params = {"limit": limit}
	r = requests.get(order_url, params=params, auth=get_auth(token))
	if r.status_code < 200 or r.status_code > 299:
		raise Exception(f"got status code {r.status_code}. content was \"{r.content}\"")
	
	con_json = r.json()
	out = {r_id: None for r_id in req_ids} # defaults to None if we do not find it.
	orders = con_json["orders"]
	for order in orders:
		if not order["request_id"] in req_ids:
			continue
		# otherwise going to add to the out dictionary
		if ("_type" in order) and (order["_type"] == "order_response"):
			out[order["request_id"]] = (True, order) # this indicates a successfully 'put in' order.
		else:
			out[order["request_id"]] = (False, order) # this indicates a non-successful order. 

	return out
	
	

# following is going to place an order from the shopify page. it will receive data formatted in a very specific way. 
# see shopify_order_processing to see what it looks like.
# returns the zinc request id.
def place_orders_shopify(token: str, address: dict, products: list, order_num: str, tx_code: str, shipping_method="cheapest", max_price=1, retailer="amazon"):
	# NOTE: we only need order_num so that we can get all the data in the json and add it in the client notes...
	if "free" in shipping_method.lower():
		shipping_method = "cheapest" #TODO: fix this. this is not right. free shipping can cost with this model. 
	
	address = _clean_address(address)
	if address is None:
		raise ValueError(f"parameter address could not be cleaned. was {address}")

	if not isinstance(products, list):
		raise ValueError(f"parameter products must be a list, not {type(products)}")
	
	json_rec = Logger.read_json(order_num)

	

	payload = {}
	payload["retailer"] = retailer
	payload["products"] = products
	payload["max_price"] = max_price
	payload["shipping_address"] = address
	payload["shipping_method"] = shipping_method 
	payload["addax"] = True
	payload["idempotency_key"] = tx_code # this is to avoid duplicate orders. 

	# temp for testing! (to avoid zma_temporarily_overloaded errors).
	payload["addax_queue_timeout"] = 12 * 60 * 60
	
	# end temp
	
	payload["client_notes"] = json_rec

	order_url = ZINC_API_LINK + "/orders"

	r = requests.post(order_url, auth=get_auth(token), data=json.dumps(payload))

	if r.status_code < 200 or r.status_code > 299:
		raise Exception(f"got bad status code: {r.status_code}. content was \"{r.content}\" ({str(datetime.now())}).")

	try:
		con_dict = r.json()
	except Exception as e:
		raise Exception(f"failed to convert content to json, raised \"{str(e)}\" ({str(datetime.now())})")
	
	if not("request_id") in con_dict:
		raise Exception(f"did not find request_id in the json. json was \"{con_dict}\" ({str(datetime.now())})")

	# return req_id. 
	return con_dict["request_id"]


# FOLLOWING IS NOT FUNCTIONAL, BUT IS A START. 
# in order to know when to fulfill an order, we really need to parse the string of the status (which we got from other method...)
# this next method will return a somewhat complicated nested dict object. here is how it will go:
# output dict
	# key "summary_info"
	# value is another dict
		# keys are product_id's
		# values are total number that has been shipped for that prod id
	
	# key "tracking_objects"
	# value is another dict
		# keys are merchant_order_id's. 
		# values are another dict. 
			# key tracking_url is tracking_url
			# key delivery_status is delivery status (this is one per merchant_order_id)
			# key "products"
			# value is a dict
				# keys are product_id's in this tracking_object
				# value is another dict
					# key "quantity"
					# value is number shipped (only in this tracking_object)
	
# THIS IS NOT FUNCTIONAL
# JUST A START
def extract_shipping_from_status(status: dict):
	# do some checking.
	if not isinstance(status, dict):
		try:
			status = json.loads(str(status))
		except Exception as e:
			raise ValueError(f"parameter status must be a dict (or a json str object). was not dict, so tried json.loads(). this raised \"{str(e)}\"")
	
	# assume that what we need is there. if it is not, it will raise a key error which is pretty self explanatory. 
	tracking_objects_raw = status["tracking"]
	# now we can begin looking. we want to keep track of the summary_info throughout this. 
	sum_info = {}
	tracking_objects_clean = {}
	for track_obj in tracking_objects_raw:
		merch_order = {}
		merch_order["merchant_order_id"] = {"merchant_order_id": track_obj["merchant_order_id"], "delivery_status": track_obj["delivery_status"]}
		products = {}
		for prod_id in track_obj["product_ids"]:
			if not prod_id in products:
				products[prod_id] = 1
			else:
				products[prod_id] += 1 # indicates another.
			# no matter what update the global info. 
		# above is info specific to an merchant order
		# keys for val will be product id's. we now go through to get the 
		tracking_objects_clean[track_obj["merchant_order_id"]] = {}



if __name__ == "__main__":
	pass
	
