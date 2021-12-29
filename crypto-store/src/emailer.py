#!/usr/bin/env python3

import os
from os import path
import time as time_
import json
from datetime import datetime

import imaplib
import ssl # not sure what version this is. built in?
import smtplib
import email
from email.message import EmailMessage

from secrets import CredsManager


def get_testing_name_pw():
	creds = CredsManager.get_email_creds()
	return (creds["name"], creds["password"])

# class can both read and send emails
# most of class should not be accessed from outside, which is why start with _
class Emailer(object):
	USERNAME, PASSWORD = get_testing_name_pw()

	def __init__(self, start=True):
		try:
			start = bool(start)
		except:
			start = True # default.
		
		self.__read_server = None
		self.__send_server = None
		if start:
			self._open_both()

	# properties for basic info
	@property
	def _is_read_open(self):
		return not(self.__read_server is None)

	@property
	def _is_send_open(self):
		return not(self.__send_server is None)

	@property 
	def _are_both_open(self):
		return(self._is_read_open and self._is_send_open)

	# methods for opening and closing. 
	def _open_read(self):
		if self._is_read_open:
			return False # already open
		self.__read_server = imaplib.IMAP4_SSL("imap.gmail.com")
		self.__read_server.login(Emailer.USERNAME, Emailer.PASSWORD)
		return True

	def _open_send(self):
		if self._is_send_open:
			return False # did not open
		port = 465  # For SSL
		context = ssl.create_default_context()
		self.__send_server = smtplib.SMTP_SSL("smtp.gmail.com", port, context=context)
		self.__send_server.login(Emailer.USERNAME, Emailer.PASSWORD)
		return True
		
	def _open_both(self):
		return((self._open_read() and self._open_send())) # returns False if one fails.
	
	def _close_read(self):
		# for closing read server and logging out. set to None after success. 
		# only close if open.
		if not(self._is_read_open):
			return False 
		try:
			self.__read_server.close()
		except:
			pass # sometimes above fails (if none selected)
		self.__read_server.logout()
		del self.__read_server # TODO: does this work?
		self.__read_server = None
		return True

	def _close_send(self):
		# for closing send server (quit)
		# only quit if open
		if not(self._is_send_open):
			return False
		self.__send_server.quit()
		del self.__send_server
		self.__send_server = None
		return True

	def _close_both(self):
		if self._is_read_open:
			self._close_read()
		
		if self._is_send_open:
			self._close_send()

	# actual use cases for sending and receiving email.
	def move_emails(self, from_mb: str, to_mb: str, white_list: list, black_list: list, delete=False):
		# this method is for moving multiple emails between inboxes. subjects is a list of substrings. 
		# emails with those substrings as part of their subject will be moved.
		# if any substring is in multiple subjects, we move those all to a special mailbox for such a case (as well as the original to_mb)
		if not isinstance(white_list, list):
			try:
				white_list = [str(white_list)]
			except:
				return -1

		if not isinstance(black_list, list):
			try:
				black_list = [str(black_list)]
			except:
				return -1
		# above is for single search terms.

		# do NOT want both black_list and white_list to be non-empty
		if (len(white_list) != 0) and (len(black_list) != 0):
			raise ValueError("cannot have both white_list and black_list (leave one as []).")
		
		if not('\"' in from_mb):
			from_mb = f"\"{from_mb}\""
		
		if not('\"' in to_mb):
			to_mb = f"\"{to_mb}\""

		#NOTE: IMPORTANT! here we do a last second test to make sure we are not moving ANYTHING from the "all email history" box. i.e. not deleting.
		if (from_mb == "\"all email history\""):
			delete = False

		# either way (black list or white list) we are going to construct the same search string. 
		# so we relabel whichever one. 
		if len(white_list) != 0:
			subj_list = white_list
		else:
			subj_list = black_list
		
		#NOTE: special circumstance. if "" is in the list, we want the query string to be ALL
		if "" in subj_list:
			query_str = "ALL"
		elif len(subj_list) == 1:
			query_str = f"(SUBJECT \"{subj_list[0]}\")"
		else:
			query_str = "(OR"
			for subj in subj_list:
				query_str += f" (SUBJECT {subj})"
		
			query_str += ")"
		
		self._open_read() # this only acts if necc.

		status, messages = self.__read_server.select(from_mb)
		if status != "OK":
			raise Exception("failed to select from_mb.")
		
		num_messages = int(messages[0])
		# next search.
		search_res = self.__read_server.search("UTF-8", query_str)
		if search_res[0] != "OK":
			raise Exception(f"failed to search for query_str: \"{query_str}\"")

		matches = [num_str for num_str in search_res[1][0].decode().split()] # this is a list of strings.
		if len(white_list) > 0:
			message_set = ','.join(matches)
			num_moved = len(matches)
			
		else:
			# go through range of numbers (we have num_messages already) and add ones not in matches
			message_set = ""
			for i in range(1, num_messages+1): # start at 1
				if not(str(i) in matches):
					message_set += f"{i},"
			num_moved = num_messages - len(matches)
			if num_moved > 0:
				# trim off last ,
				message_set = message_set[0:-1]
		
		if num_moved == 0:
			return 0 # do not want to try to move none. will fail
		
		# now that we have the message set it's pretty easy. 
		self.__read_server.copy(message_set, to_mb)
		if delete:
			self.__read_server.store(message_set, '+FLAGS', '\\Deleted')
			self.__read_server.expunge()
			
		return num_moved

	# returns list of EmailMessage's from a mailbox mb.
	def fetch_all_emails(self, mb: str):
		# mb should be encased in literal "" if not
		if not('"' in mb):
			mb = f"\"{mb}\"" 
		
		self._open_read() # only acts if necc.
		# following can raise Exceptions
		status, messages = self.__read_server.select(mb)
		if status != "OK":
			raise Exception(f"failed to select mailbox {mb}")
		
		num_messages = int(messages[0])
		# next search.
		
		if num_messages == 0:
			return([])
		query_str = f"{1}:{num_messages + 1}"
		res, full_msg_data = self.__read_server.fetch(query_str, "(RFC822)")
		if status != "OK":
			raise Exception(f"failed to fetch all emails from mailbox {mb}. query was \"{query_str}\"")

		out = []
		for i in range(num_messages):
			# for some reason we index by 2...'
			msg = email.message_from_bytes(full_msg_data[i*2][1])
			out.append(msg)
		
		return out
	
	# if force_attach is True, raises exception when cannot attach the file. 
	def send_email(self, to: str, subj: str, body: str, attached=None, force_attach=False):
		self._open_send() # only acts if necc

		try:
			force_attach = bool(force_attach)
		except:
			force_attach = False

		# first check if sending an attachment, then if that attachment is valid.
		# special case if forcing to attach.
		if not(attached is None):
			# try in case not str. if exception, just set to None (unless forcing to attach)
			try:
				if not path.exists(attached):
					raise Exception
			except:
				if force_attach:
					raise Exception(f"failed to attach {attached}. check if path exists.")
				attached = None

		
		msg = EmailMessage()
		msg.set_content(body)

		msg['From'] = Emailer.USERNAME
		msg['To'] = to
		msg['Subject'] = subj
		if not(attached is None):
			with open(attached, 'rb') as f:
				attached_content = f.read()
			# want pretty file name, if possible to extract.
			try:
				file_nm = attached[attached.rindex('/')+1:]
			except:
				file_nm = attached
			try:
				subtype = attached[attached.rindex('.')+1:]
			except:
				subtype = "bin" #TODO: find better default?
		
			try:
				msg.add_attachment(attached_content, maintype="application", subtype=subtype, filename=file_nm)
			except Exception as e:
				# only raise this back if we are forcing the attachment 
				if force_attach:
					raise Exception(f"could not add attachment (was forced). raised \"{str(e)}\"")
			
	
		self.__send_server.send_message(msg)
		
	# dunder methods. these make sure the connection is ALWAYS closed at end of program.
	def __del__(self):
		self._close_both()
		
	def __enter__(self):
		return self

	def __exit__(self, exception_type, exception_val, exception_traceback):
		self._close_both()
	

if __name__ == "__main__":
	print(email.__file__)
	
