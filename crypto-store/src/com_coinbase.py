#!/usr/bin/env python3

import requests
import json

from secrets import CredsManager


creds = CredsManager.get_coinbase_creds()
SECRET_API_KEY = creds["api_secret"]

HEADERS = {"X-CC-Api-Key": SECRET_API_KEY, "X-CC-Version": "2018-03-22", "Content-Type": "application/json"} # should content-type be here? unsure. 


# This is  one of the functions most used with the shopify store. 
# returns a list of timeline events. most recent will be the last one. 
def get_timeline(chg_code: str):
	# chg should be a charge code. 
	url = f"https://api.commerce.coinbase.com/charges/{chg_code}"
	con_dict = json.loads(requests.get(url, headers=HEADERS).content)
	timeline = con_dict["data"]["timeline"]
	return timeline

# NOTE: all following methods are not actually used in the program (the cancel ones--last two--could be used for an emergency)
# These methods are functional, but they are not used with the shopify store (shopify does most of this on its own)


# TODO: following could get unmanageable. Need to implement only grabbing till hit an expired one in the future?
def get_all_charge_codes():
	# we want to get all of the charge codes (duh), as well as their associated timelines.
	# we will store in dict as keypair... code: {"last_status": mostRecentUpdate, "timeline": wholeTimeLine}

	# we can get all the info we need in one go. 
	

	url = "https://api.commerce.coinbase.com/charges/?limit=100" # get most possible. 
	r = requests.get(url, headers=HEADERS)
	if r.status_code > 299:
		print(f"Uhoh, at beg of get_all_charge_codes got {r.status_code}. Content was {r.content}")

	con_dict = json.loads(r.content)
	pagination = con_dict["pagination"]
	# first if total == yielded then we have already grabbed everything. 
	only_one_check = False
	if pagination["total"] == pagination["yielded"]:
		only_one_check = True
	
	
	out = {}
	next_uri = "place holder"
	while not(next_uri is None):
		for charge in con_dict["data"]:
			# have code and timeline already. Just need most recent / last status
			code = charge["code"]
			timeline = charge["timeline"]
			last_status = timeline[-1]["status"]
			out[code] = {"last_status": last_status, "timeline": timeline}
		if only_one_check:
			break # no need for fancy while loop, just wasting requests
		
		# now re-request with the next uri
		next_uri = con_dict["pagination"]["next_uri"]
		# a bit clunky but cannot re-request it 
		if not(next_uri is None):
			r = requests.get(next_uri, headers=HEADERS)
			if r.status_code > 299:
				print(f"Uhoh, in end of get_all_charge_codes got {r.status_code}. Content was {r.content}")

			con_dict = json.loads(r.content) # ready to continue looking through on next iteration. 

	return out


# add a charge with no price. Not sure of a use case for this, but the function should work.
def add_charge_no_price(nm: str, desc: str):
	payload = {"name": str(nm), "description": str(desc), "pricing_type": "no_price"}
	r = requests.post("https://api.commerce.coinbase.com/charges", headers=HEADERS, data=json.dumps(payload))
	if r.status_code > 299:
		print(f"Uhoh, in add_charge_no_price got {r.status_code}. Content was {r.content}")
		return None
	con_dict = json.loads(r.content)
	print(f"Added: {con_dict['data']['code']}")
	return con_dict["data"]["code"]


# add a charge with a fixed price. This seems more useful, but again, it is not neccessary to use with the shopify store; shopify creates all the charges.
def add_charge_fixed_price(nm: str, desc: str, price: float, curr: str, meta={}):
	# curr must be BTC or USD (will add support later)
	try:
		curr = str(curr)
		curr = ''.join(curr.split())
		curr = curr.upper()
		if not(curr in ("USD", "BTC")):
			raise Exception
		nm = str(nm)
		desc = str(desc)
		price = float(price)
		if price <= 0.0:
			raise Exception
		meta = dict(meta)
	except:
		print("Failed to add charge.")
		return None

	payload = {"name": nm, "description": desc,  "metadata": meta, "local_price": {"amount": price, "currency": curr}, "pricing_type": "fixed_price" }
	#payload = {"name": nm, "description": desc,  "metadata": meta, "pricing_type": "fixed_price", "pricing": {"local": {"amount": price, "currency": curr}}}
	r = requests.post("https://api.commerce.coinbase.com/charges", headers=HEADERS, data=json.dumps(payload))
	if r.status_code > 299:
		print(f"Uhoh, in add_charge_fixed_price got {r.status_code}. Content was {r.content}")
		return None
	con_dict = json.loads(r.content)
	print(f"Added: {con_dict['data']['code']}")
	return con_dict["data"]["code"]


# gets the url that one can access a charge at. This is not neccessary since shopify just redirects to the url. 
def return_hosted_url(chg_code: str):
	url = f"https://api.commerce.coinbase.com/charges/{chg_code}"
	
	try:
		con_dict = json.loads(requests.get(url, headers=HEADERS).content)
		pause = True
		return(con_dict["data"]["hosted_url"])
	except:
		return None


# returns the title and description of a charge. not really useful with a shopify store, since there will be no description and the title will just be the store name.
def get_title_and_desc(chg_code: str):
	url = f"https://api.commerce.coinbase.com/charges/{chg_code}"
	
	try:
		con_dict = json.loads(requests.get(url, headers=HEADERS).content)
		
		title = con_dict["data"]["name"]
		desc = con_dict["data"]["description"]
		return {"title": title, "name": title, "nm": title, "desc": desc, "description": desc} # just in case forget the names
	except:
		return None



# this cancel method is not currently used, but can be called manually if an order is messed up or something similar. 
def cancel_charge(chg_code: str):
	url = f"https://api.commerce.coinbase.com/charges/{chg_code}/cancel"
	r = requests.post(url, headers=HEADERS)
	if r.status_code > 299:
		try:
			con_dict = json.loads(r.content)
		except:
			print(f"Uhoh, in cancel_charge got {r.status_code}. Content was {r.content}")
			return False 

		try:
			if con_dict["error"]["message"] == "can only cancel a NEW charge":
				print("Uhoh, tried to cancel a non-NEW charge.")
				
			elif con_dict["error"]["message"] == "Not found":
				print(f"Uhoh, could not find (to cancel) charge with code {chg_code}.")
			return False
		except:
			return False # false indicates failed

	con_dict = json.loads(r.content) 
	# we want to check that this charge is now expired. 
	charge = con_dict["data"]
	timeline = charge["timeline"]
	last_status = timeline[-1]["status"]
	if last_status != "CANCELED":
		raise Exception(f"Expected last status to be CANCELED, not {last_status}.")
	
	return True # succeeded 


# this method can be called in an emergency, or during rough rough testing. It just cancels every single open charge. 
def emergency_cancel_all():
	# first get all the charges 
	to_cancel = [] # list of codes

	charge_codes = get_all_charge_codes()
	for code, val in charge_codes.items():
		last_status = val["last_status"]
		if last_status == "NEW":
			to_cancel.append(code)
	
	print("Cancelling all orders (possible emergency).")
	i = 1
	for code in to_cancel:
		output = f"Cancelling {code} ({i}/{len(to_cancel)})... "
		try:
			succ = cancel_charge(code)
			if succ == False:
				raise Exception
			output += "Succeeded"
		except:
			output += "Failed"
		print(output)
		i += 1



if __name__ == "__main__":
	pass