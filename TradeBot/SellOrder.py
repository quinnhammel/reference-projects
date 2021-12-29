
"""
File info:
  This file contains the SellOrder class. This class is even more naive than the BuyOrder class. 
  This is because a SellOrder will try to sell the whole holding that is fed in as a parameter. If the portfolio wishes to sell part of a holding, it will be split within gen_sell_order.

  Once the SellOrder sells successfully, it stores the price it sold at and how many it sold. It then sets its OptionHolding to have 0 contracts. Part of the reason we do this, is although the OptionHolding instance no longer has any actual contracts, it will contain the price we paid for that bundle. We can use this in the portfolio class.
"""


class SellOrder(object):

  """
  Variables:
    self.__oh, should be an OptionHolding instance, only really have a dirty way of checking this.
    self.__lim_price, the limit price for this sale.
    self.__num_sold, number that were sold. This initializes to 0 and updates to the number sold after the sale goes through.

    self.__price_sold_at, price that the contracts were sold at. This initializes to None and updates to the price after the sale is successful.

  Properties:
    self.oh, returns self.__oh.
    self.lim_price, returns self.__lim_price.
    self.num_sold, returns self.__num_sold.
    self.price_sold_at, returns self.__price_sold_at
    self.has_been_executed, returns True if this sale order has been successfully executed, false otherwise. 

  Methods:
    self.try_to_sell(), attempts to sell the options at the limit price using the api. If it does, it sets self.__num_sold to the number sold and self.__price_sold_at
  """

  def __init__(self, oh, lim_price=None):
    #oh should be an OptionHolding. Unfortunately, we cannot import it, so we have to use a dirty workaround.
    if (str(type(oh)) != "<class '__main__.OptionHolding'>"):
      raise ValueError("parameter oh must be an OptionHolding.")

    #lim_price can be None, or a positive float.
    if not(lim_price is None or (isinstance(lim_price, float) and (lim_price > 0))):
      #the above is a little messy, but should work.
      raise ValueError("parameter lim_price must be None or a positive float.")
    
    self.__oh = oh
    self.__lim_price = lim_price
    self.__num_sold = 0
    self.__price_sold_at = None

  #basic properties for accessing
  @property
  def oh(self):
    return self.__oh
  
  @property
  def lim_price(self):
    return self.__lim_price

  @property
  def num_sold(self):
    return self.__num_sold
  
  @property
  def price_sold_at(self):
    return self.__price_sold_at
  
  @property
  def has_been_executed(self):
    #we know that the order has been executed when self.__num_sold > 0, self.__price_sold_at is no longer None, and self.__oh.num_owned == 0. Theoretically, we could return True from one of these. For now, we will check all three just to be careful.
    #TODO: find a different way to do this?
    return ((self.__num_sold > 0) and (not self.__price_sold_at is None) and (self.__oh.num_owned == 0))
  
  #methods
  def try_to_sell(self):
    #this method will call into the API to try to sell for the limit price.
    #TODO: implement this part with API.
    
    #if we already sold, we do not want to try
    if self.has_been_executed:
      return True

    success = False #here, success will be True if the options were sold, False otherwise

    if success:
      price_sold_at = 0.05 #here we grab this from the API if the sale went through

      #we now update everything to indicate this contract has been finished.
      self.__price_sold_at = price_sold_at
      self.__num_sold = self.__oh.num_owned
      self.__oh._set_num_owned(0) #this is pretty much the only place we should call this.
      return True
    else:
      #just return False
      return False

