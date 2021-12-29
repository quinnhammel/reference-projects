import config
from MarketDateTime import MarketDateTime as MDT
from StockTracker import StockTracker as ST
from api import API
from BuyOrder import BuyOrder


"""
File info:
  this file contains the OptionTracker class.

  this class will be used to track the prices of an option. It contains a StockTracker instance within itself, which tracks the stock that the option relies on. It also records the strike price, expiration date, shares per contract of the option, and whether the option is a put or a call.

  Most of the implementation in regards to actually fetching prices is empty, as it will use the API's cacheing system. 


  This class will contain several properties/methods which are technically redundant, for conveniance's sake. For example, if ot is an OptionTracker: the call ot.get_stock_price_moment(mdt=None) is functionally equivalent to calling ot.stock_tracker.get_price_moment(dt=None). This is just for convenience.

  NOTE: Options are by convention measured in price per share. So, an option that has 100 shares per contract, at $0.10 per share, will have a price of $0.10, not $10.00 (even though selling the contract would yield $10.00 = 100 * $0.10)
"""

#CONSTANTS *********************************************************************

PUT = config.PUT
CALL = config.CALL
DEFAULT_SPC = config.DEFAULT_SHARES_PER_CONTRACT #default amount of shares per contract.

#OptionTracker clas ************************************************************

class OptionTracker(object):

  """
  Variables:
    self.__stock_tracker, StockTracker instance to record stock's value.

    self.__put_or_call, flag for whether this option being tracked is a put or a call. Values can be PUT or CALL (given in constants above, from config.py).

    self.__strike_price, strike price of the option.

    self.__expiration_date, expiration date of the option. Should be a MarketDateTime in the future.

    self.__shares_per_contract, number of shares per contract, defaults to DEFAULT_SHARES_PER_CONTRACT (in constants above, from config.py)

  Properties:
    (functionally neccessary):
      self.stock_tracker, returns self.__stock_tracker
      self.put_or_call, returns self.__put_or_call
      self.strike_price, returns self.__strike_price
      self.expiration_date, returns self.__expiration_date
      self.shares_per_contract, returns self.__shares_per_contract
      self.last_price_moment, returns the last PriceMoment for this option cached by the API.

    (redundant, but nice):
      self.stock_ticker, returns self.__stock_tracker.ticker
      self.stock_full_name, returns self.__stock_tracker.full_name
      self.stock_last_price_moment, returns self.__stock_tracker.last_price_moment
      self.is_put, returns True if instance is a put, False otherwise
      self.is_call, returns True if instance is a call, False otherwise.
      self.time_till_expiration, returns TimeDelta till expiration.
  
  Methods:
    (normal/instance):
      self.get_price_moment(mdt=None), returns the PriceMoment at mdt for this option from the API.
      self.get_stock_price_moment(mdt=None), returns self.__stock_tracker.get_price_moment(dt). Sort of redundant but nice.

      self.gen_buy_order(num_contracts, lim_price=None), returns an instance of BuyOrder for this option being tracked. num_contracts must be a positive int, and lim_price a positive float. TODO: add support for no limit price. For now, too risky!

      self.__eq__(other), special method to test for equality of an OptionTracker. Just tests that all of its properties are equal. This will be useful for later in the portfolio class.

    (class):
      from_stock_info(ticker, full_name, p_or_c, strike_price, expiration_date, shares_per_contract), tries to build an instance of StockTracker from ticker and full_name, then returns an OptionTracker with that instance. This is an alternative constructor.

      should_buy(ot), takes in an instance of OptionTracker and returns True if it would be good to buy this option, false otherwise. After this is called, gen_buy_order would most likeley be called. TODO: eventually make this method return a float, for a ranking. Way down the line!

      
  """

  def __init__(self, stock_tracker, p_or_c, strike_price, expiration_date, shares_per_contract=DEFAULT_SPC):
    #stock_tracker must be an instance of StockTracker, ST here
    if not isinstance(stock_tracker, ST):
      raise ValueError("parameter stock_tracker must be an instance of StockTracker.")

    #p_or_c must be one of the flags
    if (p_or_c != PUT) and (p_or_c != CALL):
      raise ValueError("parameter p_or_c must have value PUT or CALL (in constants above, from config.py)")

    #strike_price must be a positive float
    if (not isinstance(strike_price, float)) or (strike_price <= 0):
      raise ValueError("parameter strike_price must be a positive float.")

    #expiration_date must be a MarketDateTime in the future. We use the clean function.

    expiration_date = MDT.clean_market_date_time_input(expiration_date)
    #here, if the date is past already, we raise a ValueError
    if (expiration_date < MDT.now()):
      raise ValueError("parameter expiration_date must be a MarketDateTime in the future.")
    

    #shares_per_contract must be a positive int.
    if (not isinstance(shares_per_contract, int)) or (shares_per_contract <= 0):
      raise ValueError("optional parameter shares_per_contract must be a positive int.")

    #set the values
    self.__stock_tracker = stock_tracker
    self.__put_or_call = p_or_c
    self.__strike_price = strike_price
    self.__expiration_date = expiration_date
    self.__shares_per_contract = shares_per_contract
  
  #basic and necessary properties, for simple protected variable access.
  @property
  def stock_tracker(self):
    return self.__stock_tracker
  
  @property
  def put_or_call(self):
    return self.__put_or_call
  
  @property
  def strike_price(self):
    return self.__strike_price

  @property
  def expiration_date(self):
    return self.__expiration_date
  
  @property
  def shares_per_contract(self):
    return self.__shares_per_contract

    #property to get the last price_moment
  @property
  def last_price_moment(self):
    #this will return the last PriceMoment that has been cached by the API.
    return None #TODO: implement this

  #extra, but conveniant properties
  @property
  def stock_ticker(self):
    return self.__stock_tracker.ticker
  
  @property
  def stock_full_name(self):
    return self.__stock_tracker.full_name
  
  @property
  def stock_last_price_moment(self):
    return self.__stock_tracker.last_price_moment
  
  @property
  def is_put(self):
    return self.__put_or_call == PUT

  @property
  def is_call(self):
    return self.__put_or_call == CALL
  
  @property
  def time_till_expiration(self):
    #return the difference between the expiration date and now.
    return (self.__expiration_date - MDT.now())
  
  #instance methods
  def get_price_moment(self, mdt=None):
    #clean mdt input
    mdt = MDT.clean_market_date_time_input(mdt)

    #here we call into the API to get the price moment. The API should tell whether it is cached. if it is, return it. If not, fetch it, cache it for later, then return it.
    return None #TODO: implement this.
  
  def get_stock_price_moment(self, mdt=None):
    #this is kind of redundant, but it is convenient for later.
    return self.__stock_tracker.get_price_moment(mdt)
  
  def gen_buy_order(self, num_contracts, lim_price=None):
    #this method will generate and return an instance of BuyOrder. 
    return BuyOrder(self, num_contracts, lim_price)
  
  #method for checking equality, useful for later
  def __eq__(self, other):
    #other must be an OptionTracker
    if not isinstance(other, OptionTracker):
      return False #definitely not equal

    #we basically want to check that all of the information matches up. So, we want the ticker, the put_or_call, the strike_price, the expiration_date, and the shares_per_contract to be equal.
    return ((self.stock_ticker == other.stock_ticker) and (self.__put_or_call == other.put_or_call) and (self.__strike_price == other.strike_price) and (self.__expiration_date == other.expiration_date) and (self.__shares_per_contract == other.shares_per_contract))

  #alternative constructor
  #from_stock_info(ticker, full_name, p_or_c, strike_price, expiration_date, shares_per_contract)
  @classmethod
  def from_stock_info(cls, ticker, full_name, p_or_c, strike_price, expiration_date, shares_per_contract=DEFAULT_SPC):
    #pretty straightforward, return instance of this class (OptionTracker) while initializing a new StockTracker using info.
    stock_tracker = ST(ticker, full_name)
    return cls(stock_tracker, p_or_c, strike_price, expiration_date, shares_per_contract)
  
  #should buy class method, bulk of algorithm goes in here.
  @classmethod
  def should_buy(cls, ot):
    if not isinstance(ot, cls):
      raise ValueError("parameter ot must be an OptionTracker.")

    #keeping this clean will be a nightmare, think carefully about how to manage the weights.
    #for now return False. Eventually can return True. EVENTUALLY add support for float rankings.
    return False #TODO: implement this function.
