#!/usr/bin/env python3

from datetime import datetime
from const import CALL, PUT

def is_valid_opt_symbol(sym: str):
	try:
		sym = str(sym)
		if len(sym) <= 5:
			raise Exception # should be much longer. 
		if sym != sym.upper():
			raise Exception # should be same upper as lower. 
	except:
		return False

	rest = None
	for i in range(5, 0, -1):
		if sym[0: i].isalpha():
			# found symbol
			rest = sym[i:]
			break
	
	if rest is None:
		return False # no symbol found in beginning. 
	
	try:
		date_raw = rest[0:6]
		date_raw_dt = datetime.strptime(date_raw, "%y%m%d")
		rest = rest[6:]
	except:
		return False # either not enough or not a valid date. 
	
	try:
		if not(rest[0] in ("C", "P")):
			raise Exception
		rest = rest[1: ]
	except:
		return False

	if len(rest) != 8 or not(rest.isdigit()):
		return False
	
	return True

# following checks if option is a call or put. 
# returns CALL for call and PUT for put
# returns None if neither.
def call_or_put(sym: str):
	if not is_valid_opt_symbol(sym):
		return None
	
	try:
		c_or_p = sym[-9:-8]
		if c_or_p == "C":
			return CALL
		elif c_or_p == "P":
			return PUT
		else:
			raise Exception
	except:
		return None

def get_date_valid_sym(sym: str):
	sym_trim = sym[0:-9]
	date_raw_str = sym_trim[-6:]
	dt = datetime.strptime(date_raw_str, "%y%m%d")
	return dt.strftime("%y-%m-%d")


if __name__ == "__main__":
	print(is_valid_opt_symbol("AAL211104P00019500"))
	print(is_valid_opt_symbol("VXX190517P00016000"))
	print(is_valid_opt_symbol("AAPL211015P00105000"))
	x = "AAL211104P00019500"
	print(x[-9:-8])