import config
from api import API
from MarketDateTime import MarketDateTime as MDT
from PriceMoment import PriceMoment as PM
from OptionTracker import OptionTracker as OT
from OptionHolding import OptionHolding
from BuyOrder import BuyOrder
from SellOrder import SellOrder

from datetime import timedelta
import collections #for set

"""
  Rough attempt. Important things:
    simple model, will only buy one of each, etc.
    class can be instantiated with lists of trackers, holdings.
    also instantiated with a simulator object to access money currently tied up (NECCESSARY???)
    has instance variable mdt, which can be set to something in the past, or None to indicate current.
    Iterate method that does all of trading for one cycle takes in a timedelta. If mdt is None it gets ignored. If not, it updates mdt to the new value.
    Clean methods for sell orders and buy orders, that weed out ones that have already been executed. THEY WILL BE CALLED A LOT, PROBABLY TOO MUCH, consider dealing with them first for speed preformances.
    THIS CLASS TRACKS STUFF BY THE BID PRICE.
"""
class Portfolio(object):
    #init method will take in lots of arguments. There needs to be a simulator instance and a list of optiontrackers. All others are optional. If no mdt is passed in, it indicates that the portfolio will be operating in current time.
  def __init__(self, simulator, trackers, **kwargs):
    self.__simulator = None
    self.__trackers = []
    self.__pending_buys = []
    self.__holdings = []
    self.__pending_sells = []

    #TODO: ADD CHECKING TYPE FOR SIMULATOR!!!!
    self.__simulator = simulator 

    #We want to be pretty careful here. We verify that val is a list, that only contains option trackers, and that there are no duplicates.
    if not isinstance(trackers, list):
      raise ValueError("parameter trackers must be a list of OptionTrackers.")
    trackers = set(trackers) #This removes duplicates.
    for ot in trackers:
      if not isinstance(ot, OT):
        raise ValueError("found a non-OptionTracker in parameter trackers.")
      self.__trackers.append(ot)


    #We now go through the optional parameters.

    for key, val in kwargs.items():
      #want key and val to be lower case, but also want original values.
      orig_key = key
      orig_val = val
      key = key.lower()
      val = val.lower()

      #branch off into cases now
      if key == "pending_buys" or key == "buys" or key == "buy_orders":
        #we want to be careful here, again.
        if not isinstance(val, list):
          raise ValueError("parameter pending_buys must be a list of BuyOrders.")
        val = set(val) #This removes duplicates.
        for bo in val:
          if not isinstance(bo, BuyOrder):
            raise ValueError("found a non-BuyOrder in parameter pending_buys.")
          self.__pending_buys.append(bo)
      
      elif key == "holdings" or key == "ohs":
        #we want to be careful here, again.
        if not isinstance(val, list):
          raise ValueError("parameter holdings must be a list of OptionHoldings.")
        val = set(val) #This removes duplicates.
        for oh in val:
          if not isinstance(oh, OptionHolding):
            raise ValueError("found a non-OptionHolding in parameter holdings.")
          self.__holdings.append(oh)

      elif key == "pending_sells" or key == "sells" or key == "sell_orders":
          #we want to be careful here, again.
        if not isinstance(val, list):
          raise ValueError("parameter pending_sells must be a list of SellOrders.")
        val = set(val) #This removes duplicates.
        for so in val:
          if not isinstance(so, SellOrder):
            raise ValueError("found a non-SellOrder in parameter pending_sells.")
          self.__holdings.append(so)
      elif key == "mdt" or key == "time":
          self.__mdt = MDT.clean_market_date_time_input(val)
      else:
          raise ValueError(f"Invalid key: {orig_key}.")
        
    #we now clean buys and sells for later
    self.clean_buys()
    self.clean_sells()


  def clean_buys(self):
    pass

  def clean_sells(self):
    pass


  @property
  def floating_buy_capital(self):
    #returns the amount of money 'floating' in buys, ie tied up in buy orders that have not yet executed.
    float_cap = 0.0
    for bo in self.__pending_buys:
      if not bo.has_been_executed:
        float_cap += bo.num_contracts * (bo.option_tracker.shares_per_contract * bo.lim_price)
    return float_cap
    
  @property
  def floating_sell_capital(self):
    #similar, but for pending sells
    float_cap = 0.0
    for so in self.__pending_sells:
      if not so.has_been_executed:
        float_cap += so.oh.num_owned * (so.oh.shares_per_contract * so.lim_price)
    return float_cap
    

  @property
  def liquid_capital(self):
    #returns the current liquid assets. Again, current could be in the past if mdt is in the past.
    #TODO: add simulator CALL!
    sim_capital = 2.0 #this will be the amount the simulator says we have in liquid capital. We need only to subtract the floating_buy_capital, which counts as liquid in the simulator, but not for our purposes.
    return sim_capital - self.floating_buy_capital
  
  @property
  def illiquid_capital(self):
    #this will total up the worth of all options owned, those in holdings and sell orders not executed, as well as the floating_buy_capital we will use to purchase them.
    #NOTE: THIS METHOD USES BID PRICES, WHICH MEANS IT IMPLICITLY ASSUMES THE SELL AT BID MODEL
    #NOTE: THIS USES THE MDT TIME VARIABLE!

    cap = 0.0
    for oh in self.__holdings:
      cap += oh.num_owned * (oh.num_contracts * oh.get_price_moment(self.__mdt).bid)
    
    for so in self.__pending_sells:
      oh = so.oh
      cap += oh.num_owned * (oh.num_contracts * oh.get_price_moment(self.__mdt).bid)
    
    cap += self.floating_buy_capital
  
  