from OptionTracker import OptionTracker
from PriceMoment import PriceMoment as PM
from SellOrder import SellOrder
from MarketDateTime import MarketDateTime
from datetime import timedelta

"""
File info:
  This file contains the OptionHolding class. It is just an OptionTracker that is owned.

  As such, it inherits from OptionTracker. It then has a couple extra variables to keep track of the number of contracts owned, the PriceMoment they were purchased on.
  
  There is also a static method to determine whether to sell this OptionHolding, and a way to create a sell order.

  The only other tricky thing is the constructor. It will take in an OptionTracker and then call the super() constructor on that instance's properties.

  TODO: consider __price_actually_paid implementation.


  NOTE: the most unforgiving part of the whole buy/sell protocol is between the OptionHolding and SellOrder class. In the gen_sell_order method, the holding is split in two if part of it is being sold. This means if you call gen_sell_order and lose the input, like by not storing it, you have created a discrepancy and messed up the whole system.
"""

class OptionHolding(OptionTracker):

  """
  Variables: 
    self.__num_owned, number of contracts owned. 
      NOTE:Can be set using a method, but should not be set unless under very special circumstances.
    self.__pm_at_purchase, a PriceMoment of when the option was bought.
    self.__price_actually_paid, can be feed in, defaults to self.__pm_at_purchase

  Properties:
    self.num_owned, returns self.__num_owned
    self.pm_at_purchase, returns self.__pm_at_purchase.
    self.price_actually_paid, returns self.__price_actually_paid. Again, this defaults to pm_at_purchase.ask

  Methods:
    instance/normal:
      self.gen_sell_order(num_to_sell=None, lim_price=None), generates a sell order for this holding. If num_to_sell is None, it defaults to the total number of contracts held.
      NOTE: call this function carefully, it will change the number owned. Selling two out of five contracts would switch this instance to contain 3=5-2, then return a SellOrder for 2. 

      self._set_num_owned(new_num), resets the num_owned. NOTE: DO NOT CALL THIS FUNCTION! It should only be called under the circumstance that some or all of the options are sold in this holding. This will only occur within the SellOrder class.

    class:
      should_sell(oh), determines whether an OptionHolding instance should be sold.

      NOTE: this class will be able to call should_buy, which could be confusing. This also might be useful. TODO: consider this.
  
  """

  #mainly just inherit from the class. The parameter price_actually_paid is optional. If not provided, or not a float, it will take the value of pm_at_purchase.ask.
  def __init__(self, ot, num_owned, pm_at_purchase, price_actually_paid=None):
    #ot must be an OptionTracker.
    if not isinstance(ot, OptionTracker):
      raise ValueError("parameter ot must be an OptionTracker.")
    
    #we now call the super().__init__ with ot's information.
    super().__init__(ot.stock_tracker, ot.put_or_call, ot.strike_price, ot.expiration_date, ot.shares_per_contract)

    #num_owned must be a positive int
    if (not isinstance(num_owned, int)) or (num_owned <= 0):
      raise ValueError("parameter num_owned must be a positive int.")

    #pm_at_purchase must be a PriceMoment
    if not isinstance(pm_at_purchase, PM):
      raise ValueError("parameter pm_at_purchase must be a PriceMoment.")

    #if price_actually_paid is not a positive float, it defaults to pm_at_purchase.ask, since we will most likely be paying the asking price.
    if not(isinstance(price_actually_paid, float)) or (price_actually_paid <= 0):
      price_actually_paid = pm_at_purchase.ask
    
    #set the variables
    self.__num_owned = num_owned
    self.__pm_at_purchase = pm_at_purchase
    self.__price_actually_paid = price_actually_paid

  #properties for accessing data
  @property
  def num_owned(self):
    return self.__num_owned

  @property
  def pm_at_purchase(self):
    return self.__pm_at_purchase

  @property
  def price_actually_paid(self):
    return self.__price_actually_paid
  
  #instance methods
  #NOTE: calling gen_sell_order will change the OptionHolding instance itself! proceed with caution.
  def gen_sell_order(self, num_to_sell=None, lim_price=None):
    #if num_to_sell is None, it means all of the options in this bundle.
    if (num_to_sell is None):
      num_to_sell = self.__num_owned

    #num_to_sell must be an int from 1 to self.__num_owned
    if (not isinstance(num_to_sell), int) or (num_to_sell < 1) or (num_to_sell > self.__num_owned):
      raise ValueError("num_to_sell must be None or an int in range from 1 to num_owned.")

    #Strictly speaking, we do not need to check the lim_price here, it gets checked in the SellOrder constructor. However, we do want to check it before we change any of the nums, so that we can never get stuck and lose track of holdings.
    #lim_price can be None, or a positive float.
    if not(lim_price is None or (isinstance(lim_price, float) and (lim_price > 0))):
      #the above is a little messy, but should work.
      raise ValueError("parameter lim_price must be None or a positive float.")


    #we now change the number owned within this instance, and create a new instance of OptionHolding with num_to_sell 
    self.__num_owned -= num_to_sell
    new_holding = OptionHolding(self, num_to_sell, self.__pm_at_purchase, self.__price_actually_paid) #CAN WE DO THIS??? IT MIGHT BE A LITTLE WEIRD TO PASS IN AN OPTIONHOLDING BUT I THINK WE CAN TODO
    return SellOrder(new_holding, lim_price) #return the sell order.

  
    #DO NOT CALL THIS!!!
  
  def _set_num_owned(self, new_num):
    #DO NOT CALL THIS METHOD UNLESS YOU ARE SELLING THE OPTIONS!
    #new_num must be a nonnegative int, and must also be less than the current num. This will only be called when selling the holding.

    if not isinstance(new_num, int):
      raise ValueError("parameter new_num must be int. Are you sure you mean to call this method? Tread with caution.")

    if (new_num > self.__num_owned) or (new_num < 0):
      raise ValueError("parameter new_num can only be within the range 0, current num. Are you sure you mean to call this method? Tread with caution.")

    #can finally set it.
    self.__num_owned = new_num
  
  #should sell class method, bulk of actual algorithm goes in here.
  @classmethod
  def should_sell(cls, oh):
    if not isinstance(oh, cls):
      raise ValueError("parameter oh must be an OptionHolding.")

    #keeping this clean will be a nightmare, think carefully about how to manage the weights.
    #for now return False. Eventually can return True. EVENTUALLY add support for float rankings.
    return False #TODO: implement this function.


