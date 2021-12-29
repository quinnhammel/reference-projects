"""
So the important thing is stocks and options will be cached by price moment
So they'll use that date time thing, then a price, bid, ask.
And it's up to you how to separate the different stocks and options.
Stocks could just be by ticker, options you need ticker, expiration date, and a strike price.
For the expiration date, you'll have to check like if the days are equal since the api will manage time with a different class
"""


import config
import secret
import yfinance as yf
from alpha_vantage.timeseries import TimeSeries
from PriceMoment import PriceMoment
from MarketDateTime import MarketDateTime
from datetime import datetime

PLATFORM = config.PLATFORM

SIMULATOR = "SIMULATOR"
AMERITRADE = "AMERITRADE"

ts = TimeSeries(key=secret.ALPHA_VANTAGE_API_KEY)

class API:
  def __init__(self, platform=PLATFORM, cache={}):
    
    """
    Variables:
      self.__platform, direction on where to get send API requests to. Ex: "SIMULATOR" means data comes from yfinance and requests go to simulator class.
      self.__cache, stores data previously requested in order to lower API requests. By default is empty.
    """
    
    if not isinstance(platform, str):
      raise ValueError("platform parameter must be a string")

    if not isinstance(cache, dict):
      raise ValueError("cache parameter must be a dictionary")


    self.__platform = platform
    self.__cache = cache

  def write_cache(self):
    pass # will work on this later

  # returns stock meta data
  def get_stock_info(self, ticker: str, dt=None):
    if (self.__platform == SIMULATOR):
      ticker = ticker.upper()
      stock = yf.Ticker(ticker)
      yf_info = stock.info

      info = {
        "name": yf_info.shortName,
        "description": yf_info.longBusinessSummary,
        "volume": yf_info.volume
      }

      return info

  # processes API data into a single PriceMoment object
  def get_stock_price(self, ticker: str, dt=None):
    if (self.__platform == SIMULATOR):
      data, meta_data = ts.get_intraday(symbol=ticker, interval='5min')

      if (dt == None):
        mdt = MarketDateTime.from_str(list(data.keys())[0])
        price = float(data[list(data.keys())[0]]["1. open"])

      if (dt != None):
        mdt = MarketDateTime.from_str(str(dt))
        mdt_alt_format = str(mdt)
        mdt_alt_format = list(mdt_alt_format)
        mdt_alt_format[10] = " "
        mdt_alt_format = "".join(mdt_alt_format)
        mdt_alt_format = mdt_alt_format[:-6]
        price = float(data[mdt_alt_format]["1. open"])
        

      return PriceMoment(mdt, price)




if __name__ == "__main__":
  nice = API()