import pytz
from datetime import timedelta

EAST_TZ = pytz.timezone("EST") #timezone constant
TIME_MARGIN = timedelta(minutes=1) #margin where two times are considered equal, can be changed later.
VALID_TICKERS = ["PHO", "ENDP"]
NOW = "now" #used for calling functions to use current datetime.
PUT = True #flag value for OptionTracker class. 
CALL = False #flag value for OptionTracker class. (these two values must be different!)
DEFAULT_SHARES_PER_CONTRACT = 100 #this is pretty standard for most options.
PLATFORM="SIMULATOR"

DES_LIQUIDITY = 0.3 #desired proportion of liquid value.