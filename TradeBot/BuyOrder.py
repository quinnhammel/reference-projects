import config
from MarketDateTime import MarketDateTime as MDT
from api import API
from datetime import timedelta

"""
File info:
  This file contains the class BuyOrder. 

  This class is more complicated and requires special attention by the routine that will use it. Essentially, a BuyOrder is initialized with an OptionTracker instance, a num to buy, and a lim price.

  An instance can then be called (bo.attempt_buy()) to attempt to buy the option, using the API. (This method returns True if it succeeds, false if otherwise)

  NOTE: this requires careful usage, since the price of the option could change making the limit impossible to buy at.

  Once the order goes through, one can get an OptionHolding instance from the instance, which represents the now officially owned options.
"""


class BuyOrder(object):

  """
  Variables:
    self.__option_tracker, instance of OptionTracker for the option we wish to purchase.
    self.__num_contracts, the number of contracts to attempt to purchase.
    self.__lim_price, the limit price. TODO: implement no limit price maybe some day?
    self.__options_bought, the options purchased by this sale order, will be an instance of OptionHolding. This variable will remain None until the options are successfully bought (see methods below).

  Properties:
    self.option_tracker, returns self.__option_tracker
    self.num_contracts, returns self.__num_contracts
    self.lim_price, returns self.__lim_price
    self.options_bought, returns self.__options_bought
    self.has_been_executed, returns True if this order has been executed, False otherwise.
  
  Methods:
    self.try_to_buy(), attempts to purchase the options at the limit price using the api. If it does, it sets self.__options_bought to those options and returns True. Returns False if it does not succeed.
  """

  def __init__(self, option_tracker, num_contracts, lim_price=None):
    #option tracker must be an OptionTracker (OT)
    #BECAUSE OF IMPORT ISSUES, MUST USE THIS DIRTY WORKAROUND.
    if (str(type(option_tracker)) != "<class '__main__.OptionTracker'>"):
      raise ValueError("parameter option_tracker must be an instance of OptionTracker.")

    #num_contracts must be a positive int
    if (not isinstance(num_contracts, int)) or (num_contracts <= 0):
      raise ValueError("parameter num_contracts must be a positive int.")

    #lim_price can be None, or a positive float.
    if not(lim_price is None or (isinstance(lim_price, float) and (lim_price > 0))):
      #the above is a little messy, but should work.
      raise ValueError("parameter lim_price must be None or a positive float.")

    #set variables
    self.__option_tracker = option_tracker
    self.__num_contracts = num_contracts
    self.__lim_price = lim_price
    self.__options_bought = None

  #properties
  @property
  def option_tracker(self):
    return self.__option_tracker

  @property
  def num_contracts(self):
    return self.__num_contracts
  
  @property
  def lim_price(self):
    return self.__lim_price
  
  @property
  def options_bought(self):
    return self.__options_bought
  
  @property
  def has_been_executed(self):
    #the order has been executed if options_bought is no longer None
    return not(self.__options_bought is None)

  #methods
  def try_to_buy(self):
    #this method will call into the API to try to buy for the limit price.
    #TODO: implement this part with API.

    #if we have already bought, we do not want to attempt again
    if self.has_been_executed:
      return True

    success = False #here, success will be True if the options were bought, False otherwise

    if success:
      #make self.__options_bought the options we bought. Then, return True
      #TODO: implement this part of the skeleton right after OptionHolding
      return True
    else:
      #just return False
      return False


