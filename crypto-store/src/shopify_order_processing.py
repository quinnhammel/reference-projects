#!/usr/bin/env python3

import json
import time as time_
from os import path
from copy import deepcopy

import imaplib
import email
from email.message import EmailMessage

from logger import Logger
from shopify import order_num_to_both, fulfill_whole_order_rough
from const import ZINC_MAX_COST, MAX_QUANT, REPO_PATH
from com_coinbase import get_timeline
from zinc import place_orders_shopify
from emailer import Emailer
from zinc import get_order_statuses
from secrets import CredsManager


email_creds = CredsManager.get_email_creds()
EMAIL_NM, EMAIL_PW = (email_creds["name"], email_creds["password"])
ZINC_TOKEN = CredsManager.get_zinc_creds()["api_secret"]
DEFAULT_PHONE_NUM = CredsManager.get_default_zinc_phone_num()["name"] # this is the default phone number used in zinc orders. Maybe fix this later. 
ERROR_EMAIL = CredsManager.get_error_email_creds()["name"]



#TODO: issue with getting orders immediately after they are received (a little lag in Shopify's system can cause issues.)
# GLOBAL NOTES
# the whole system is about moving emails to different inboxes depending on where they are in the ordering process.
# now the flow will be
	# order placed --> INBOX (from shopify's end)
		# INBOX --> new pending payment (if can find an order num in the subj)
			
		# INBOX --> non-order (if cannot find an order num in the subj)
	# cache coinbase info from order_num. store this and keep checking periodically for completed payment
	# after completed payment
		# if expired --> payment expired
		# if completed --> payment completed awaiting zinc init
		# if not expired or completed --> unknown error coinbase charge
	# in payment completed awaiting zinc init:
		# try parsing address. if error --> error initiating zinc (also log)
		# try placing order. if internal exception --> error initiating zinc (also log)
		# if success placing order --> pending zinc confirmation (log req_id)
	# in pending zinc confirmation:
		# as soon as a status object gets returned --> pending zinc shipping (also log)
		# if an error gets returned --> zinc side error (also log)

	# in the loop, also init all in "payment completed awaiting zinc init"
	# once initiated, goes to "pending zinc shipping"
	# check this box also for shipping confirmations from zinc
	# once done, goes to "completed order"

	#NOTE: we will take the least risks around the zinc end. i.e. we will check for the request id everytime (instead of caching it...) TODO: consider if this is a good idea.

	# also: any email --> all email history (to be safe)

def msg_to_dict(email_msg):
	subj = email_msg["subject"]
	sender = email_msg["from"]
	body = ""
	# only append payloads to body IF they do not have html in them...
	for payload in email_msg.get_payload():
		if isinstance(payload, str):
			text = payload
		else:
			text = payload.get_payload()
		# a bit rough of a test but fine for now
		if not("/>" in (''.join(text.split()))):
			body += str(text)
	return {"subj": subj, "subject": subj, "sender": sender, "body": body, "from": sender}


# md is a message dict. dict containing subject/subj, body, from/sender
def _check_msg_dict(md: dict):
	# just check that dict and has keys.
	if not isinstance(md, dict):
		raise ValueError(f"param md must be a dict, not type {str(type(md))}. msg_dict was {str(md)}")
	
	# keys: "subj" , "subject" , "sender" , "from" , "body"
	# {"subj": subj, "subject": subj, "sender": sender, "body": body, "from": sender}
	# do more advanced key checking just in case.
	
	# subject
	if ("subj" in md):
		md["subject"] = md["subj"]
	elif "subject" in md:
		md["subj"] = md["subject"]
	else:
		raise ValueError(f"param md must contain \"subj\" or \"subject\" as a key. md was {str(md)}")
	
	# from/sender
	if "sender" in md:
		md["from"] = md["sender"]
	elif "from" in md:
		md["sender"] = md["from"]
	else:
		raise ValueError(f"param md must contain \"sender\" or \"subject\" as a key. md was {str(md)}")

	# final check for body. 
	if not("body" in md):
		raise ValueError(f"param md must containt \"body\" as a key. md was {str(md)}")

	return # all good. changes dict in place so no need to return dict



# TODO: figure out the phone number issue. (the zinc api requires a phone number, but you cannot require a phone number from shopify. it can only be optional. For now default is taken from credentials on AWS. See secrets.py)
# in below: max_quantity is the quantity number above which we trigger an exception. this is to avoid erroneous huge orders.
# input is expected to be valid. It should be a message dict (created using msg_to_dict(email_msg)). The email message should be an order notification from shopify. If it is not, the method will likely raise an exception. 
def _parse_new_order_msg_dict(md: dict, max_quantity=MAX_QUANT):
	if max_quantity <= 0:
		max_quantity = MAX_QUANT
	
	if isinstance(md, EmailMessage):
		md = msg_to_dict(md)

	_check_msg_dict(md)
	body = md["body"]
	body = body.replace('\t', '').replace('\r', '')
	lines = body.split('\n')
	while '' in lines:
		lines.remove('')
	
	# for convenience and efficiency we are going to store a copy of the lines in lower case 
	lines_lower = [ln.lower() for ln in lines]

	out = {} # return the data we get

	pause = True
	# first check for risk of fraud.
	high_risk_fraud = False
	for ln in lines_lower:
		if "high risk of fraud" in ln:
			high_risk_fraud = True
			break
		
	out["high_risk_fraud"] = high_risk_fraud
	
	uq_item_count = 0
	for ln in lines_lower:
		if "sku" in ln:
			uq_item_count += 1

	out["uq_item_count"] = uq_item_count # strictly speaking this is not neccessary to store. 


	# we are going to go through and get the orders first. 
	# have to go through line by line. 
	# but we will store the orders in the format that zinc will want later
	# we can have json files to get other info from the product code
	products = [] 


	# first: grab product keys from json file. 
	with open(path.join(REPO_PATH, "data", "products.json"), 'r') as f:
		sku_to_codes = json.loads(''.join(f.readlines()))
	
	order_summary_index = -1
	for i in range(len(lines_lower)):
		if "order summary" in lines_lower[i]:
			order_summary_index = i
			break
	
	if order_summary_index == -1:
		raise Exception("failed parse. could not find order summary line.")

	for item_num in range(uq_item_count):
		title_index = order_summary_index + 1 + 4 * item_num # this is just how to get to the right line
		quant_line = lines[title_index+1]
		if not "D7 " in quant_line:
			raise Exception("failed parse. could not find D7 (times symbol) in quantity line.")
		quant_str = quant_line[quant_line.index("D7 ") + 3:]
		# strip it in case. 
		quant_str = ''.join(quant_str.split())
		quantity = int(quant_str)
		if quantity > max_quantity:
			raise Exception(f"parse failed. specified quantity ({quantity}) is larger than max quantity ({max_quantity}). does this order look like a typo?")
		
		if quantity <= 0:
			raise Exception(f"parse failed. found invalid quantity: {quantity}")

		# next just want to get the SKU (and then product code)
		sku_line = lines[title_index+2]
		if not "SKU" in sku_line:
			raise Exception("failed parse. could not find \"SKU\" in sku line.")
		
		sku = sku_line[sku_line.index("SKU: ")+5:]
		sku = ''.join(sku.split()) # just in case. 
		# want to get prod code. 
		if not sku in sku_to_codes:
			raise Exception(f"parse failed. could not find SKU {sku} in json dict of products. dict was:\n\n{sku_to_codes}\n\n")
		# otherwise all good. 
		prod_code = sku_to_codes[sku]

		# can now add product
		products.append({"product_id": prod_code, "quantity": quantity})

	out["products"] = products # add the products to the return value. 

		
	# next we want to grab shipping info and payment info (for later implementing non-coinbase payment)
	payment_proc_index = -1
	for i in range(len(lines_lower)):
		if "payment processing" in lines_lower[i]:
			payment_proc_index = i
			break

	if payment_proc_index == -1:
		raise Exception("failed parse. could not find payment processing line.")

	out["payment_method"] = ''.join(lines_lower[payment_proc_index + 2].split())
	out["delivery_method"] = lines[payment_proc_index + 4].strip() #NOTE: the delivery method needs to be worked on later.
	# want to construct address now.
	address = {} 
	full_name = lines[payment_proc_index + 6].strip()
	out["full_name"] = full_name # store this for book keeping (in case more than first or last name)
	names_split = full_name.split(' ')
	if len(names_split) == 0:
		raise Exception(f"failed parse. length of names split was 0. full name was {out['full_name']}")
	
	address["first_name"] = ''.join(names_split[0].split())
	if len(names_split) == 1:
		# only first name.
		address["last_name"] = ""
	else:
		address["last_name"] = ''.join(names_split[-1].split())
	
	# before we continue we need to find the length of the address (to determine if valid and if second address line.)
	# address starts at full_name line. payment_proc_index + 6
	# ends before line with "Shopify" in it
	address_length = 0
	i = payment_proc_index+6
	ln = lines_lower[i]
	while (not("shopify") in ln) and (i < len(lines)):
		i += 1
		ln = lines_lower[i]
		address_length += 1
	
	# now we can get the address lines.
	# first line is same no matter what.
	address["address_line1"] = lines[payment_proc_index + 7].strip()
	if address_length == 6:
		address["address_line2"] = ""
		offset = 0
	elif address_length == 7:
		address["address_line2"] = lines[payment_proc_index + 8].strip()
		offset = 1
	else:
		raise Exception(f"failed parse. address was too long or too short. should have 6 or 7 lines, not {address_length}")
	
	city = lines[payment_proc_index + offset + 8].strip()
	if ',' in city:
		city = city[0:city.rindex(',')] # want to cut out the ',' from the end if it is there

	address["city"] = city
	# state is annoying since we need to convert from full state to acronym
	state_long_form = lines[payment_proc_index + offset + 9].strip()
	
	# want to open up the states file.
	try:
		with open(path.join(REPO_PATH, "data", "states.json"), 'r') as f:
			states = json.loads(''.join(f.readlines()))
	except Exception as e:
		raise Exception(f"failed opening data/states.json file. raised \"{str(e)}\".")

	if not(state_long_form in states):
		raise Exception(f"parse failed. invalid state (long form): \"{state_long_form}\"")

	address["state"] = states[state_long_form]
	address["zip_code"] = lines[payment_proc_index + offset + 10].strip()
	#NOTE: only works in US
	address["country"] = "US"
	#TODO: fix phone number issues. 
	address["phone_number"] = DEFAULT_PHONE_NUM

	out["shipping_address"] = address
	return out

# expects clean input (name, pw)
def _process_new_in_inbox(emailer: Emailer, name=EMAIL_NM, pw=EMAIL_PW):
	print("processing new in inbox...")
	curr = time_.time()
	# first going to move all order messages into the new pending payment box and non-payments to non-order box
	# we do not delete yet. we will do this in a second.
	emailer.move_emails("INBOX", "new pending payment", ["Orderx"], [], False) # whitelist picks up what we want. blacklist does not pick up anything. False means do not delete from inbox
	# next move non-orders
	emailer.move_emails("INBOX", "non-order", [], ["Orderx"], False) # now whitelist picks up nothing, black list picks up all non-orders.

	# now we can move ALL emails into "all email history" . we also delete from inbox here.
	# NOTE: never remove from all email history. ever.
	emailer.move_emails("INBOX", "all email history", [""], [], True) # empty str is substr of everything. so this will pick up all emails. True means we delete
	elapsed = time_.time() - curr
	
	print(f"\ttook {round(elapsed, 2)} s.")



def _process_new_pending_payment(emailer: Emailer, mb='"new pending payment"', name=EMAIL_NM, pw=EMAIL_PW):
	print("processing new pending payment...")
	curr = time_.time()
	last = curr
	all_emails = emailer.fetch_all_emails(mb)
	elapsed = time_.time() - last
	#print(f"\t\tfetching mailbox took {round(elapsed, 2)}s")
	
	if all_emails is None:
		raise Exception(f"encountered error. fetch_all_emails returned None for mb={mb}")
	
	
	req_in_json = {"order_num": None, "order_id": None, "cb_chg_code": None}.keys() # this makes it easy to check if the keys are present.
	# lists for chg categories (where to move emails later)
	to_completed = []
	to_expired = []
	to_unknown = []

	for msg in all_emails:
		last = time_.time()
		subj = msg["Subject"]
		try:
			order_num = subj[subj.index('#')+1: subj.index(" placed")]
		except:
			continue # failed to read subject line, probably an issue. just leave it there for now.
		data_on_rec = Logger.read_json(order_num)
		if req_in_json <= data_on_rec.keys():
			cb_chg_code = data_on_rec["cb_chg_code"]
		else:
			# the data is not there. we fetch it now. 
			# NOTE: IMPORTANT! There is a weird exception that can occur when payments are fetched too soon. so, we except and continue if there is an issue.
			#TODO: find better solution
			try:
				chg_data = order_num_to_both(order_num)
			except:
				continue
			cb_chg_code = chg_data["cb_chg_code"]
			# write the data down for later.
			Logger.write_json(order_num, {"order_num": order_num, "order_id": str(chg_data["order_id"]), "cb_chg_code": cb_chg_code})
		elapsed = time_.time() - last
		#print(f"\t\tpossibly fetching cb_chg info took {round(elapsed, 2)}s.")
		last = time_.time()
		# by here we have a cb_chg_code. we now fetch the statuses of the coinbase charges.
		timeline = get_timeline(cb_chg_code)
		elapsed = time_.time() - last
		#print(f"\t\tgetting timeline took {round(elapsed, 2)}s.")

		try:
			last_status = timeline[-1]["status"]
		except:
			raise Exception(f"could not access last element of timeline for order num {order_num}, cb_chg {cb_chg_code}. timeline was {timeline}")
	
		# if not new or pending needs to be moved.
		if not(last_status in ("NEW", "PENDING")):
			# if we get here, the email will be moved. 
			# the question is what the dest (destination) will be. diff for COMPLETED, EXPIRED, and all else
			# add these to the lists for movement later.
			if last_status == "COMPLETED":
				to_completed.append(order_num)
			elif last_status == "EXPIRED":
				to_expired.append(order_num)
			else:
				to_unknown.append(order_num)
			Logger.write_json(order_num, {"payment_termination_status": last_status})

	last = time_.time()
	# once we get here we need to do the moving. 
	# we are careful here. mainly avoid duplicates.
	if len(to_completed) != 0:
		to_completed = list(set(to_completed)) # avoid duplicates
		# to_completed can now serve as a whitelist for the move.
		emailer.move_emails(mb, "payment completed awaiting zinc init", to_completed, [], True) # delete from curr box too
		# blacklist won't match anything

	# same as above for expired and unknown
	if len(to_expired) != 0:
		to_expired = list(set(to_expired))
		emailer.move_emails(mb, "payment expired", to_expired, [], True)
	if len(to_unknown) != 0:
		to_completed = list(set(to_completed))
		emailer.move_emails(mb, "unknown error coinbase charge", to_unknown, [], True)

	elapsed = time_.time() - last
	#print(f"\t\tmoving emails took {round(elapsed, 2)}s.")
	elapsed = time_.time() - curr
	print(f"\ttotal took {round(elapsed, 2)} s.")
	

def _process_awaiting_zinc_init(emailer: Emailer, mb='"payment completed awaiting zinc init"', max_price=ZINC_MAX_COST, name=EMAIL_NM, pw=EMAIL_PW):
	print("processing awaiting zinc init...")
	curr = time_.time()
	all_emails = emailer.fetch_all_emails(mb)

	to_error_init_box = []
	to_pending_zinc_confirmation = []
	for msg in all_emails:
		msg_dict = msg_to_dict(msg)
		subj = msg_dict["subj"]
		try:
			order_num = subj[subj.index('#')+1:subj.index(" placed")] # for logging. NOTE: assumes the order email is an order email
		except:
			continue # just in case.
		try:
			parsed_data = _parse_new_order_msg_dict(msg_dict)
			Logger.write_json(order_num, {"address_parsing": {"failed_parse": False, "parse_error": None, "parsed_data": parsed_data}})
			
		except Exception as e:
			# we get here we mark down we failed the parse.
			Logger.write_json(order_num, {"address_parsing": {"failed_parse": True, "parse_error": str(e), "parsed_data": None}})
			
			# now we need to add this to the list we're going to move to the error box
			to_error_init_box.append(order_num)
			continue
		
		# get here we want to try to place the order.
		# first: we are going to generate an idempotency/tx_code
		# do a safety check: if there is already a tx_code, we do not generate a new one.
		rec_con = Logger.read_json(order_num)
		if "tx_code" in rec_con:
			# already present
			tx_code = rec_con["tx_code"]
		else:
			# not present, make and log now.
			tx_code = Logger.gen_tx_code() 
			Logger.write_json(order_num, {"tx_code": tx_code})
			
		try:
			req_id = place_orders_shopify(ZINC_TOKEN, parsed_data["shipping_address"], parsed_data["products"], order_num, tx_code, "cheapest", max_price)
			Logger.write_json(order_num, {"zinc_call_internal": {"failed": False, "error": None, "request_id": req_id, "req_id": req_id}, "request_id": req_id, "req_id": req_id})
			# in above write both req_id and request_id just for convenience
			to_pending_zinc_confirmation.append(order_num)
		except Exception as e:
			Logger.write_json(order_num, {"zinc_call_internal": {"failed": True, "error": str(e), "request_id": None, "req_id": None}, "request_id": None, "req_id": None})
			to_error_init_box.append(order_num)
			

	# now move the emails. 
	if len(to_error_init_box) != 0:
		to_error_init_box = list(set(to_error_init_box)) # avoid duplicates.
		emailer.move_emails(mb, "error initiating zinc", to_error_init_box, [], True) # to_error_init_box is a list of order nums. as such it is a good whitelist. True means we delete from this box. 
	if len(to_pending_zinc_confirmation) != 0:
		to_pending_zinc_confirmation = list(set(to_pending_zinc_confirmation))
		emailer.move_emails(mb, "pending zinc confirmation", to_pending_zinc_confirmation, [], True)

	elapsed = time_.time() - curr
	print(f"\ttook {round(elapsed, 2)} s.")



# following is a bit complex in terms of mailbox transfer. takes in the pending zinc confirmation emails. 
# if no zinc request id found -->N LOST or MISSIG zinc request id (should happen rarely)
# if completed --> zinc confirmed pending shipping
# if not completed (and no other error) --> stays
# if error --> zinc side error (remove from here; error is non-pending one)
	# if max_price error also --> zinc possible dry run completed
# if we get None as a status --> not found in zinc system (also stays here in case something changes)
#TODO: refactor this method. possibly by rewriting the get_statuses method in zinc.py
#TODO: ADD SUPPORT FOR MULTIPLE PRODUCTS
def _process_awaiting_zinc_confirm(emailer: Emailer, mb='"pending zinc confirmation"'):
	print("processing awaiting zinc confirmation (already init)...")
	curr = time_.time()
	all_emails = emailer.fetch_all_emails(mb)
	subjects = [msg["Subject"] for msg in all_emails]
	order_nums = []
	for subj in subjects:
		try:
			order_nums.append(subj[subj.index('#')+1: subj.index(" placed")])
		except:
			continue # in case something goes wrong. 

	# next we want to try to get the corresponding request ids for all these orders. 
	# if we do not find one, we move to the lost box. 
	to_lost_or_missing = []
	order_req_ids = {}
	for order_num in order_nums:
		data = Logger.read_json(order_num)
		try:
			req_id = data["zinc_call_internal"]["request_id"] # (key error if not yet initiated)
			if req_id is None:
				raise Exception # indicates the internal call failed. 
			order_req_ids[order_num] = req_id
		except:
			# either call failed or it is not found in the json. either way goes to lost.
			to_lost_or_missing.append(order_num)
	

	# now we make the zinc request. NOTE: if this fails something has gone wrong. 
	statuses = get_order_statuses(ZINC_TOKEN, order_req_ids.values())
	
	to_not_found = []
	to_completed_pending_shipping = []
	to_zinc_error = []
	to_possible_dry_run = []
	for order_num, req_id in order_req_ids.items():
		status = statuses[req_id]
		if status is None:
			to_not_found.append(order_num)
			continue
		
		done, content = status
		if done:
			# here we check for a status update indicating that the order has been CONFIRMED. 
			# we check to see that status_updates is there. 
			if not("status_updates" in content):
				raise Exception(f"could not find status_updates in content for req_id {req_id}. content was \"{content}\"")
			# done says that request is in system. confirmed means it has been confirmed
			confirmed = False
			for status_update in content["status_updates"]:
				try:
					# use try in case type not there. if it is, we clean the string just in case.
					if ''.join(status_update["type"].lower().split()) == "order.confirmed":
						confirmed = True
						break
				except:
					continue 
			
			# only move to completed if done (indicates confirmed)
			# otherwise continue in outer loop and do not move anything.
			if confirmed:
				to_completed_pending_shipping.append(order_num)
			continue # this is for outer loop

		# basic checking of data. this stuff should be here.
		# TODO: see if this is an issue and if it is make a separate mailbox for it
		if not("_type" in content):
			raise Exception(f"could not find _type in order content for req_id {req_id}. content was \"{content}\"")
		if not(content["_type"] == "error"):
			raise Exception(f"expected _type error, instead got {content['_type']}. req_id was {req_id}. content was \"{content}\"")
		if not("code" in content):
			raise Exception(f"could not find code in order content for req_id {req_id}. content was \"{content}\"")
		
		
		# now actual checking
		if content["code"] == "request_processing":
			continue # this is still processing and should be kept here. 
		
		# get here, have an actual error. 
		to_zinc_error.append(order_num)
		if content["code"] == "max_price_exceeded":
			to_possible_dry_run.append(order_num)

	#TODO: remove temporary gaurdarails or make it neater. 
	
	# once we get here time to do the moving. have to be careful since there is some overlap. 
	# first we do moves that do NOT get deleted. 
	if len(to_not_found) != 0:
		to_not_found = list(set(to_not_found))
		emailer.move_emails(mb, '"not found in zinc system"', to_lost_or_missing, [], False) # no delete.
		# this is in case anything changes in a later run.

		# do error emails (TODO: is this a common thing or not?)
		for o_num in to_not_found:
			subj = f"ZINC MEDIUM ERROR. ORDER {o_num} WAS NOT FOUND (not lost or missing, though)"
			body = f"THIS REQUIRES YOUR ATTENTION."
			attached = Logger.gen_json_path(o_num)
			# want this part to be exception safe. 
			# first send trying to attach. if this fails, try without it. if this fails, continue. 
			try:
				emailer.send_email(ERROR_EMAIL, subj, body, attached)
			except Exception as e:
				body += f"\n\nALSO FAILED TO ATTACH, raised \"{str(e)}\""
				try:
					emailer.send_email(ERROR_EMAIL, subj, body)
				except:
					continue # want to be completely exception safe. 
	
	if len(to_possible_dry_run) != 0:
		to_possible_dry_run = list(set(to_possible_dry_run))
		emailer.move_emails(mb, '"zinc possible dry run completed"', to_possible_dry_run, [], False)
		# do not delete above because also goes to more generic error box. 

	if len(to_zinc_error) != 0:
		to_zinc_error = list(set(to_zinc_error))
		emailer.move_emails(mb, '"zinc side error"', to_zinc_error, [], True) 
		# delete since we already moved subset (dry run)
		# send an email for each.
		for o_num in to_zinc_error:
			subj = f"ZINC CRITICAL ERROR. ORDER {o_num} HAD A ZINC SIDE ERROR."
			body = f"THIS REQUIRES YOUR ATTENTION."
			attached = Logger.gen_json_path(o_num)
			# want this part to be exception safe. 
			# first send trying to attach. if this fails, try without it. if this fails, continue. 
			try:
				emailer.send_email(ERROR_EMAIL, subj, body, attached)
			except Exception as e:
				body += f"\n\nALSO FAILED TO ATTACH, raised \"{str(e)}\""
				try:
					emailer.send_email(ERROR_EMAIL, subj, body)
				except:
					continue # want to be completely exception safe. 

	if len(to_lost_or_missing) != 0:
		to_lost_or_missing = list(set(to_lost_or_missing))
		emailer.move_emails(mb, '"LOST or MISSING zinc request id"', to_lost_or_missing, [], True) 
		# delete since this is a critical issue. 
		# NOTE: we send a log email to ERROR_EMAIL (for each order.)
		# this is temporary for manual inspection. 
		for o_num in to_lost_or_missing:
			subj = f"ZINC CRITICAL ERROR. ORDER {o_num} WAS LOST OR MISSING"
			body = f"THIS REQUIRES YOUR ATTENTION."
			attached = Logger.gen_json_path(o_num)
			# want this part to be exception safe. 
			# first send trying to attach. if this fails, try without it. if this fails, continue. 
			try:
				emailer.send_email(ERROR_EMAIL, subj, body, attached)
			except Exception as e:
				body += f"\n\nALSO FAILED TO ATTACH, raised \"{str(e)}\""
				try:
					emailer.send_email(ERROR_EMAIL, subj, body)
				except:
					continue # want to be completely exception safe. 

	
	
	if len(to_completed_pending_shipping) != 0:
		to_completed_pending_shipping = list(set(to_completed_pending_shipping))
		emailer.move_emails(mb, '"zinc confirmed pending shipping"', to_completed_pending_shipping, [], True)
		# also delete above. 
	elapsed = time_.time() - curr
	print(f"\ttook {round(elapsed, 2)} s.")

# NOTE: FOLLOWING IS NOT FULLY FUNCTIONAL, and DOES NOT WORK PROPERLY!
# TODO: combine this with above??
#NOTE: IMPORTANT! This method is not as exception safe as above. this is because it assumes that the system has only moved to here if everything else has worked well. 
# once finished moves to "zinc shipped pending delivery"
# TODO: implement following
def _process_zinc_confirmed_pending_shipping(emailer: Emailer, mb='"zinc confirmed pending shipping"'):
	print("processing zinc confirmed pending shipping...")
	return # NOTE: BELOW HAS UNRELIABLE BEHAVIOR
	curr = time_.time()
	all_emails = emailer.fetch_all_emails(mb)
	subjects = [msg["Subject"] for msg in all_emails]
	order_nums = []
	for subj in subjects:
		try:
			order_nums.append(subj[subj.index('#')+1: subj.index(" placed")])
		except:
			continue # in case something goes wrong. 
	
	# from here on we are assuming that the sytem has been correct up to this point
	# TODO: find a better way to handle all of this. 
	order_req_ids = {}
	for order_num in order_nums:	
		req_id = Logger.read_json(order_num)["zinc_call_internal"]["request_id"]
		order_req_ids[order_num] = req_id
	
	# now get status content.
	statuses = get_order_statuses(ZINC_TOKEN, order_req_ids.values())
	to_shipped = []
	for order_num, req_id in order_req_ids.items():
		status = statuses[req_id] # might be None if something has gone very wrong.
		done, content = status # done ought to be True.
		# here we check for a status update indicating that the order has been CONFIRMED. 
		
		# done says that request is in system. confirmed means it has been confirmed
		confirmed = False
		for update in status["status_updates"]:
			if ''.join(update.lower().splite()) == "shipment.shipped":
				to_shipped.append(order_num) 
			# otherwise do nothing. 
	
	# want to try to fulfill all the orders that are necessary. 
	temp = deepcopy(to_shipped)
	to_shipped = []
	for order_num in to_shipped:
		order_id = Logger.read_json(order_num)["order_id"]
		try:
			fulfillment_info = fulfill_whole_order_rough(order_id)
			Logger.write_json(order_num, {"shopify_fulfillment": {"fulfillment_success": True, "exception_raised": None, "fulfillment_info": fulfillment_info}})
			to_shipped.append(order_num)
		except Exception as e:
			Logger.write_json(order_num, {"shopify_fulfillment": {"fulfillment_success": False, "exception_raised": str(e), "fulfillment_info": None}})

	if len(to_shipped) != 0:
		to_shipped = list(set(to_shipped))
		emailer.move_emails(mb, "zinc shipped pending delivery", to_shipped, [], True)
	
	elapsed = time_.time() - curr
	print(f"\ttook {round(elapsed, 2)} s.")




		
# this just does one check. this will be in the __main__ if statement here, and the script will be called by a lambda rule. 
def do_iteration(emailer: Emailer):
	_process_new_in_inbox(emailer)
	_process_new_pending_payment(emailer)
	_process_awaiting_zinc_init(emailer)
	_process_awaiting_zinc_confirm(emailer)
	try:
		_process_zinc_confirmed_pending_shipping(emailer)
	except Exception as e:
		print(f"failed to process awaiting shipping, raised \"{str(e)}\". NOTE: this is not yet functional.")


if __name__ == "__main__":
	with Emailer() as e:
		print("starting\n\n")
		do_iteration(e)
		print("finished")
		
	
	


