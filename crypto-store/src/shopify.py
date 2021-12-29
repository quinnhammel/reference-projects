#!/usr/bin/env python3

import time as time_
import json

import requests

from secrets import CredsManager


creds = CredsManager.get_shopify_creds()
SHOPIFY_SECRET_API = creds["api_secret"]
SHOPIFY_API_KEY = creds["api_key"]
SHOP_NAME = CredsManager.get_shop_name()["name"]


def _build_base_url(name=SHOPIFY_API_KEY, pw=SHOPIFY_SECRET_API, shop=SHOP_NAME):
	return f"https://{name}:{pw}@{shop}.myshopify.com"

# TODO: consider about support for multiple orders.
def order_num_to_id(order_num: str):
	# this is for order_num --> order_id. 
	# now... order num and id are on shopify's end for the order. the order num is the more readable one (e.g. 10002), while id is longer
	# see here: https://shopify.dev/api/admin/rest/reference/orders
	# and here for issues: https://community.shopify.com/c/Shopify-APIs-SDKs/Unable-to-retrieve-orders-via-REST-API/td-p/677019
	

	endpoint = "/admin/api/2021-07/orders.json"
	url = _build_base_url() + endpoint
	params = {"name": f"%{order_num}", "status": "any"}
	r = requests.get(url, params=params)
	
	# basic error checking. 
	if r.status_code < 200 or r.status_code > 299:
		raise Exception(f"got status code {r.status_code}. content was:\n\n{r.content}\n\n")

	# now we are going to 'prod' for the data we want, raising an exception if something goes wrong...
	con_json = r.json()
	try:
		orders = con_json["orders"]
		if len(orders) != 1:
			raise Exception("found multiple orders.")
		order = orders[0]
		return order["id"]

	except Exception as e:
		raise Exception(f"something went wrong with getting order_id. raised: \"{str(e)}\".\n\ncon_json was {con_json}\n\n")
	


def order_id_to_cb_chg_code(order_id: str):
	# now. order_id is ugly and on shopify side (returned by order_num_to_id). 
	# cb_chg_code is shorter and is from the coinbase side. 
	# this function uses some weirdly undocumented things
	# see this:
		# https://community.shopify.com/c/Shopify-APIs-SDKs/Unable-to-retrieve-orders-via-REST-API/td-p/677019
		# look at Nolan M's answer.
		# he said:
	
			# Anyone else?

			# Some further testing.

			# Used API version 2020-01. Same issue.

			# I tried /admin/orders/123123123123/transactions.json and I get the transactions list back successfully.

	endpoint = f"/admin/orders/{order_id}/transactions.json"
	url = _build_base_url() + endpoint
	r = requests.get(url)

	# basic error checking
	if r.status_code < 200 or r.status_code > 299:
		raise Exception(f"got status code {r.status_code}. content was:\n\n{r.content}")

	# similar to order_num_to_id we are going prodding for what we need. 
	con_json = r.json()

	try:
		transactions = con_json["transactions"]
		transaction = transactions[0]
		# double check we used coinbase...
		if transaction["gateway"] != "coinbase_commerce_":
			raise Exception("found non coinbase commerce gateway. not intended (for now)")

		# otherwise good to go
		return transaction["authorization"]
	except Exception as e:
		raise Exception(f"something went wrong with getting cb_chg_code from order_id. raised: \"{str(e)}\".\ncon_json was \n\n{con_json}\n\n")

def order_num_to_cb_chg_code(order_num: str):
	# order num is readable thing on shopify side. cb_chg_code is from coinbase
	return order_id_to_cb_chg_code(order_num_to_id(order_num))


# the following returns a dict with all the info needed for convenience
def order_num_to_both(order_num: str):
	order_id = order_num_to_id(order_num)
	cb_chg_code = order_id_to_cb_chg_code(order_id)
	out = {"order_id": order_id, "cb_chg_code": cb_chg_code, "cb_chg": cb_chg_code, "chg_code": cb_chg_code}
	out["order_num"] = order_num
	return out

# NOT YET FULLY FUNCTIONAL
def get_line_items(order_id: str):
	endpoint = f"/admin/api/2021-07/orders/{order_id}.json?fields=line_items"
	url = _build_base_url() + endpoint
	r = requests.get(url)
	con_json = r.json()
	line_items_rough = con_json["order"]["line_items"]
	
	out = []
	for line_item in line_items_rough:
		out.append({"id": line_item["id"]})
	return out



# NOT YET FULLY FUNCTIONAL
# TODO: elaborate on following.
# currently can only fulfill the whole order at  once...
# also only has one location from (890 Coleman) and does not have tracking...
def fulfill_whole_order_rough(order_id: str):
	url = _build_base_url() + f"/admin/orders/{order_id}/fulfillments.json"
	headers = {"Content-Type": "application/json"}
	
	line_items = get_line_items(order_id)
	payload = {"fulfillment": {"location_id": 63928008892, "tracking_numbers": [None], "notify_customer": True}}

	r = requests.post(url, data=json.dumps(payload), headers=headers)
	
	if r.status_code < 200 or r.status_code > 299:
		raise Exception(f"got status code {r.status_code}. content was:\n\n{r.content}\n\n")
	return r.json()


# NOT YET FULLY FUNCTIONAL
def get_fulfillments(order_id: str):
	endpoint = f"/admin/api/2021-07/orders/{order_id}/fulfillments.json"
	url = _build_base_url() + endpoint
	r = requests.get(url, headers={"Content-Type": "application/json"})
	print(r.json())
	 

if __name__ == "__main__":
	pass
	

	
	