import config
from MarketDateTime import MarketDateTime
from api import API

"""
File info:
  This file contains the StockTracker class. this class will be used to track prices for a certain stock. It takes in a ticker (must be a valid ticker, found in constants above from config) and a fullname and can then return PriceMoments for that stock from API calls.

  NOTE: this class is mostly empty since the API will handle the cacheing from now on.

  TODO: hook up to API.

  TODO: consider naming conventions for the stock. Ticker? Fullname? Some id number? Tickers do change...
"""

#CONSTANTS *********************************************************************

VALID_TICKERS = config.VALID_TICKERS

#StockTracker class ************************************************************

class StockTracker(object):

  """
  Variables:
    self.__ticker, the ticker for the stock, as an upper case str. Must be in VALID_TICKERS (in constants above, from config.py)

    self.__full_name, the full_name for the stock, as a str. Unsure as to whether this variable is necessary, see TODO above.

  Properties:
    self.ticker, returns the ticker
    self.full_name, returns the full_name
    self.last_price_moment, returns the last cached PriceMoment, using API.

  Methods:
    self.get_price_moment(mdt=None), returns the Stock's price_moment at that mdt (None defaults to current time).
  """

  def __init__(self, ticker, full_name):
    #ticker and full_name must be str's. ticker must be in VALID_TICKERS.
    ticker = ticker.upper()
    if not (ticker in VALID_TICKERS):
      raise ValueError("invalid ticker parameter, not in VALID_TICKERS. See config.VALID_TICKERS")
    
    if not isinstance(full_name, str):
      raise ValueError("parameter full_name must be a str.")

    self.__ticker = ticker
    self.__full_name = full_name
  
  @property
  def ticker(self):
    return self.__ticker
  
  @property
  def full_name(self):
    return self.__full_name
  
  @property
  def last_price_moment(self):
    #this will return the last PriceMoment that has been cached by the API.
    return None #TODO: implement this
  
  def get_price_moment(self, mdt=None):
    #clean mdt input
    mdt = MarketDateTime.clean_market_date_time_input(mdt)
   
    #here we call into the API to get the price moment. The API should tell whether it is cached. if it is, return it. If not, fetch it, cache it for later, then return it.
    return None #TODO: implement this.


