#!/usr/bin/env python3

import json
import boto3


# have a class for managing credentials. keeps the key pairs as private static variables. 
class CredsManager(object):
	REGION_NAME = "us-east-2"

	# private static variables.
	__EMAIL_CREDS_ID = "keep_this_secret_1"
	__COINBASE_API_CREDS_ID = "keep_this_secret_2"
	__ZINC_API_CREDS_ID = "keep_this_secret_3"
	__SHOPIFY_API_CREDS_ID = "keep_this_secret_4"
	__DEFAULT_ZINC_PHONE_NUM_CREDS_ID = "keep_this_secret_5"
	__WARNING_EMAIL_CREDS_ID = "keep_this_secret_6"
	__SHOP_NAME_CREDS_ID = "keep_this_secret_7"

	def __init__(self):
		pass # this class is not instantiated ever

	@staticmethod
	def get_creds(creds_req: str):
		# check if one of the creds we have access to. if it is we set the secret_id to it.
		# if this method fails it returns None
		try:
			creds_req = creds_req.lower() # for easier name detection. 
			if "email" in creds_req:
				# can either be default processing email or the error one. 
				if ("warning" in creds_req) or ("error" in creds_req) or ("emergency" in creds_req):
					secret_id = CredsManager.__WARNING_EMAIL_CREDS_ID
				else:
					secret_id = CredsManager.__EMAIL_CREDS_ID
			elif ("coinbase" in creds_req) or ("cb" in creds_req):
				secret_id = CredsManager.__COINBASE_API_CREDS_ID
			elif "zinc" in creds_req:
				secret_id = CredsManager.__ZINC_API_CREDS_ID
			elif "shopify" in creds_req:
				secret_id = CredsManager.__SHOPIFY_API_CREDS_ID
			elif "phone" in creds_req:
				secret_id = CredsManager.__DEFAULT_ZINC_PHONE_NUM_CREDS_ID
			elif ("shop" in creds_req) and ("name" in creds_req):
				secret_id = CredsManager.__SHOP_NAME_CREDS_ID
			else:
				raise Exception
		except:
			# phrase not found or failed .lower(), indicating not a str.
			return None

		try:
			session = boto3.session.Session()
			client = session.client("secretsmanager", region_name="us-east-2")
			creds_dict = json.loads(client.get_secret_value(SecretId=secret_id)["SecretString"])
			return creds_dict
		except:
			return None # something went wrong... 
	

	# following are just for convenience and simply call the more general get_creds method
	@staticmethod
	def get_email_creds():
		return CredsManager.get_creds("email")
	
	@staticmethod
	def get_error_email_creds():
		return CredsManager.get_creds("error email")

	@staticmethod
	def get_coinbase_creds():
		return CredsManager.get_creds("coinbase")

	@staticmethod
	def get_zinc_creds():
		return CredsManager.get_creds("zinc")

	@staticmethod
	def get_shopify_creds():
		return CredsManager.get_creds("shopify")

	@staticmethod
	def get_default_zinc_phone_num():
		return CredsManager.get_creds("phone")

	@staticmethod
	def get_shop_name():
		return CredsManager.get_creds("shop name")

if __name__ == "__main__":
	pass
