#!/usr/bin/env python3

import os
import time as time_
import json
from datetime import datetime

from const import PROJ_INFO_NM, CALL, PUT
from  util import is_valid_opt_symbol, get_date_valid_sym, call_or_put

# in general, name of the game is a few things. 
	# want to have a way to write down data efficiently
	# mainly focussed on space efficiency.
	# we do this by not copying redundant data: if no price data has changed on a security, we simply link back to that other price data
	# other than that: 
		# if something goes wrong at beginning of directory work, raise Exception (i.e. trying to overwrite something)
		# if something goes wrong later, correct it. (i.e. not finding a folder that should be there, make the folder)

# following _ helpers do NOT do input checking.
def _gen_opt_folder_path(proj_abs_path: str, opt_sym: str):
	c_or_p = call_or_put(opt_sym)
	if c_or_p is None:
		raise Exception("call_or_put failed on symbol, indicates bad symbols.")
	
	if c_or_p == CALL:
		c_or_p = "Calls"
	else:
		c_or_p = "Puts"
	
	return os.path.join(proj_abs_path, f"expir={get_date_valid_sym(opt_sym)}", c_or_p, opt_sym)

def _gen_opt_file_path(proj_abs_path: str, opt_sym: str, date_str: str):
	return os.path.join(_gen_opt_folder_path(proj_abs_path, opt_sym), f"rec_on={date_str}")


# functions for setting up folder structure at beginning of a project (only done once) and beginning of day (daily)
def setup_new_proj(proj_name: str, home_path: str, opt_syms: list):
	print("setting up new project...", end='')
	# first check the parameters for basic info. 
	try:
		proj_name = str(proj_name)
	except:
		raise ValueError("parameter proj_name must be a str.")
	
	if not os.path.isdir(home_path):
		raise ValueError("parameter home_path must be a path to a directory.")
	
	proj_abs_path = os.path.join(home_path, proj_name)
	if os.path.exists(proj_abs_path):
		raise ValueError("parameter proj_name cannot be an existing project.")
	
	try:
		opt_syms = list(opt_syms)
		for sym in opt_syms:
			if not is_valid_opt_symbol(sym):
				raise Exception
	except:
		raise ValueError("parameter opt_syms must be a list of valid option symbols.")

	opt_syms = [str(sym) for sym in opt_syms]


	# DONE with basic checking. can proceed assuming input is clean and safe.
	# next we want to extract the dates in the format %y-%m-%d from the symbols (for grouping the symbols into buckets by these)
	# we already checked that the symbols are valid so we are all good for doing this. 
	dates = []
	for sym in opt_syms:
		dates.append(get_date_valid_sym(sym))

	dates = list(set(dates)) # get rid of duplicates here. 
	
	# next we make the project folder and proj_info.json file
	os.mkdir(proj_abs_path)
	with open(os.path.join(proj_abs_path, PROJ_INFO_NM), 'w') as f:
		f.write(json.dumps({"proj_name": proj_name, "opt_syms": opt_syms}))

	# next make folders for "buckets" of options. a bucket is a expiry date.
	# keep track of paths for later (convenient)
	expir_date_paths_dict = {}
	for d in dates:
		expir_date_path = os.path.join(proj_abs_path, f"expir={d}")
		expir_date_paths_dict[d] = expir_date_path
		os.mkdir(expir_date_path)
		os.mkdir(os.path.join(expir_date_path, "Calls"))
		os.mkdir(os.path.join(expir_date_path, "Puts"))

	# next we want to make a directory for EVERY symbol that we have. 
	# we put it in Calls or Puts under the expiration date folder. 
	for sym in opt_syms:
		os.mkdir(_gen_opt_folder_path(proj_abs_path, sym))
		
	print("...finished")

# in following date_str should be of form %y-%m-%d
def setup_new_day(date_str: str, proj_name_or_abs_path, home_path=None):
	# check if date is a datetime. if so convert. after check if str and if valid. if this fails (or if not str) make today.
	print("setting up new day...", end='')
	new_line_printed = False # this is just for formatting error messages nicely.

	needs_fix = False
	if isinstance(date_str, datetime):
		date_str = date_str.strftime("%y-%m-%d")
	elif isinstance(date_str, str):
		# try to check is valid format. to do this we just convert it to datetime and back. 
		try:
			# could be %y%m%d perhaps
			if len(date_str) == 6:
				datetime.strptime(date_str, "%y%m%d").strftime("%y-%m-%d")
			else:
				datetime.strptime(date_str, "%y-%m-%d").strftime("%y-%m-%d") 
		except:
			# something went wrong. needs a fix.
			needs_fix = True
	else:
		needs_fix = True # not a str or a datetime.

	if needs_fix:
		date_str = datetime.now().strftime("%y-%m-%d")
		if not new_line_printed:
			print('\n', end='')
			new_line_printed = True # for nice formatting. 
		print(f"\tdate was fixed to {date_str}.")
			
	
	if home_path is None:
		proj_abs_path = proj_name_or_abs_path
	else:
		proj_abs_path = os.path.join(home_path, proj_name_or_abs_path)

	if not os.path.isdir(proj_abs_path):
		raise Exception(f"project not found in path {proj_abs_path}. check that project is already init.")

	# next we want to read all the symbols and create new json files for the day (if they are not present.)
	# do not want to override anything. 
	# we are assuming all the symbols in the info file will be valid.
	with open(os.path.join(proj_abs_path, PROJ_INFO_NM), 'r') as f:
		syms = json.loads(''.join(f.readlines()))["opt_syms"]


	num_folders_created = 0
	num_files_ignored = 0 # for later printing purposes
	for sym in syms:
		# check if the folder is there. if not, make it, but take note. 
		# then check if the files is there. if it is, do not make it, but take note. 
		opt_folder_path = _gen_opt_folder_path(proj_abs_path, sym)
		if (os.path.isfile(opt_folder_path)):
			raise Exception(f"found file instead of directory at path {opt_folder_path}.")

		if not os.path.exists(opt_folder_path):
			num_folders_created += 1
			os.mkdir(opt_folder_path)
		
		opt_day_rec_path = _gen_opt_file_path(proj_abs_path, sym, date_str)
		if os.path.exists(opt_day_rec_path):
			# do not want to overwrite, but count that we are not.
			num_files_ignored += 1
		else:
			with open(opt_day_rec_path, 'w') as f:
				f.write(json.dumps({}))
		
	if num_folders_created > 0:
		if not new_line_printed:
			print('\n', end='')
			new_line_printed = True
		print(f"\tcreated {num_folders_created} missing option folders.")
	
	if num_files_ignored > 0:
		if not new_line_printed:
			print('\n', end='')
			new_line_printed = True
		print(f"\tignored {num_files_ignored} day option files.")

	print("...finished")


if __name__ == "__main__":
	with open("~/Tradier/nice_opts_100_C.json", 'r') as f:
		con = json.loads(''.join(f.readlines()))
	
	syms = [o["symbol"] for o in con]
	start = time_.time()
	setup_new_proj("test_project", "~/Tradier", syms)
	elapsed_new_proj = time_.time() - start
	start = time_.time()

	setup_new_day("21-10-05", "~/Tradier/test_project")
	elapsed_new_day = time_.time() - start

	elapsed_total = elapsed_new_proj + elapsed_new_day
	print(f"elapsed time:\n\t{elapsed_new_proj * 1_000} ms (new proj)\n\t{elapsed_new_day * 1_000} ms (new day)\n\n\t{elapsed_total * 1_000} ms (total).")


