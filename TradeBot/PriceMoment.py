import config
from MarketDateTime import MarketDateTime as MDT

#this following class will be used to store prices. It stores a MarketDateTime (parameter mdt) and three floats (parameters price, bid, ask. These will be protected and accessibble via properties.

#In addition, if bid and ask are not passed in or are not floats, they default to the value of price. This is done for recording stock values, where we do not care as much about the spread. 
# TODO: will options actually have a price or just a bid and ask? possibly better to have a different class to save space in the long term?

#NOTE: a PriceMoment instance has no idea what security's price it is recording, that is up to whatever is creating the PriceMoment.

#CONSTANTS *********************************************************************

NOW = config.NOW

#PriceMoment class *************************************************************

class PriceMoment(object):

  """
  Variables:
    self.__mdt is the MasterDateTime for this PriceMoment.
    self.__price is the price, as a float.
    self.__bid is the bid price, as a float.
    self.__ask is the ask price, as a float.
  Properties:
    self.mdt, returns self.__mdt.
    self.price, returns self.__price
    self.bid, returns self.__bid
    self.ask, returns self.__ask
    self.spread, returns the spread, which is self.__ask - self.__bid
  Methods:
    instance/normal: 
      __repr__, special method which allows for a str representation of the object. Can call repr(pm) and str(pm).
      
    class:
      PriceMoment.from_str(s), returns a PriceMoment constructed from its str representation.
  """

  def __init__(self, mdt, price, bid=None, ask=None):
    #NOTE: mdt can be passed in as the value NOW (in constants, from config.NOW), which means we want the current MarketDateTime.

    #use the clean mdt method here.
    mdt = MDT.clean_market_date_time_input(mdt)    

    #price must be a float.
    if not isinstance(price, float):
      raise ValueError("price parameter must be a float.")

    #if bid or ask are not floats, they default to price.
    if not isinstance(bid, float):
      bid = price

    if not isinstance(ask, float):
      ask = price
    
    #set values
    self.__mdt = mdt
    self.__price = price
    self.__bid = bid
    self.__ask = ask

  #basic properties for returning info

  @property
  def mdt(self):
    return self.__mdt
  
  @property
  def price(self):
    return self.__price
  
  @property
  def bid(self):
    return self.__bid

  @property 
  def ask(self):
    return self.__ask
  
  @property
  def spread(self):
    return self.__bid - self.__ask
  
  #method to get str and repr.
  def __repr__(self):
    return f"(mdt={str(self.__mdt)},price={self.__price},bid={self.__bid},ask={self.__ask})"
  
  @classmethod
  def from_str(cls, pm_str):
    if not isinstance(pm_str, str):
      raise ValueError("parameter pm_str must be a str.")

    #we basically grab indices of the equals signs, and raise a valueerror if they are not found.
    try:
      mdt = MDT.from_str(pm_str[pm_str.index("mdt=")+4 : pm_str.index(",")])
      price = float(pm_str[pm_str.index("price=")+6 : pm_str.index(",bid")])
      bid = float(pm_str[pm_str.index("bid=")+4 : pm_str.index(",ask")])
      ask = float(pm_str[pm_str.index("ask=")+4 : pm_str.index(")")])
      return cls(mdt, price, bid, ask)
    except Exception as e:
      raise ValueError("invalid format for parameter pm_str.")
