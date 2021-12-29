import config
from datetime import datetime

"""
File info:
    WARNING: THIS CLASS IS BY FAR THE MOST TECHNICAL, BE CAREFUL MESSING WITH IT. TODO: consider in long term whether this is a good idea?

    This file has a class that inherits from datetime that we will use instead. We do this so that we can override the ==, <, > operators. We can make two MarketDateTime's equal if they are within a certain range, which we set in config.py.

    We also must overload the MarketDateTime.now() class method, so that it returns an instance of MarketDateTime and not datetime. The same issue makes us override the + and - operators for the class as well.

    There is also a static method called clean_market_date_time_input(mdt), which will make sure mdt is a MarketDateTime with correct timezone, otherwise raise a ValueError.

    We also add to str and from str support. If mdt is an instance of MarketDateTime, we can convert it to a str with str(mdt). If s is that str, we can call MarketDateTime.from(s)
"""

#CONSTANTS *********************************************************************

EAST_TZ = config.EAST_TZ
TIME_MARGIN = config.TIME_MARGIN #margin where two MarketDateTime's are considered equal
NOW = config.NOW

#MarketDateTime class **********************************************************
class MarketDateTime(datetime):
    #override the == operator using the __eq__ method.
    def __eq__(self, other):
        #first check that other is an instance of MarketDateTime. For now other can also be a datetime.
        #TODO: could this cause an issue? should we also check if other is a datetime?
        if (not isinstance(other, MarketDateTime)) and (not isinstance(other, datetime)):
            return False #not equal clearly
        #return True if within margin of each other.
        return (abs(other - self) < TIME_MARGIN)
    
    #override the < operator using the __lt__ method.
    def __lt__(self, other):
        #we need to first make sure that these two are not equal under our new definition.
        if (self.__eq__(other)):
            return False #cannot be less if they are equal
        #call the super method
        return super().__lt__(other) #TODO: is this really allowed though??
    
    #override the > operator using the __gt__method.
    def __gt__(self, other):
        #we need to first make sure that these two are not equal under our new definition.
        if (self.__eq__(other)):
            return False #cannot be less if they are equal
        #call the super method
        return super().__gt__(other) #TODO: is this really allowed though??
    
    #we now need to override the + operator, using the __add__ method. This ensures that the correct type is returned.
    def __add__(self, other):
        #we first call the super's __add__ method. If the result is a timedelta, nothing needs to be done. If it is a datetime, we must return a MarketDateTime instead
        output = super().__add__(other)
        if isinstance(output, datetime):
            output = MarketDateTime.from_datetime(output)
        return output
    
    #we now do the same thing for the - operator, using the __sub__method.
    def __sub__(self, other):
        #we first call the super's __sub__ method. If the result is a timedelta, nothing needs to be done. If it is a datetime, we must return a MarketDateTime instead
        output = super().__sub__(other)
        if isinstance(output, datetime):
            output = MarketDateTime.from_datetime(output)
        return output

    #overrite to_str, use isoformat for simplicity.s
    def __str__(self):
        return self.isoformat()

    #alternate constructors (next 3)
    #special helper class method for constructing a MarketDateTime from a datetime.
    @classmethod
    def from_datetime(cls, dt):
        if not isinstance(dt, datetime):
            raise ValueError("parameter dt must be a datetime.")
        
        #construct an instance of this class (MarketDateTime) identical to the datetime.
        return cls(year=dt.year, month=dt.month, day=dt.day, hour=dt.hour, minute=dt.minute, second=dt.second, microsecond=dt.microsecond, tzinfo=dt.tzinfo)
    
    #override the now method for conveniance
    @classmethod
    def now(cls):
        #call the super method, using EAST_TZ as the timezone. Then, return a MarketDateTime constructed using the from_datetime class method.
        return cls.from_datetime(super().now(tz=EAST_TZ))

    #class method for constructing from a str. Useful for cache.
    @classmethod
    def from_str(cls, str):
        output = cls.fromisoformat(str)
        #we now have to change the timezone back unfortunately. 
        return cls(year=output.year, month=output.month, day=output.day, hour=output.hour, minute=output.minute, second=output.second, microsecond=output.microsecond, tzinfo=EAST_TZ)

    #a static method to clean the input, which should be a MarketDateTime
    @staticmethod
    def clean_market_date_time_input(mdt):
        #two special cases, mdt is NOW (in constants, from config.NOW) or None. Both mean that mdt should be the current MarketDateTime.
        if (mdt == NOW) or (mdt is None):
            mdt = MarketDateTime.now()
            
        #if mdt is a str, we should try to use that class constructor. This step comes after checking if mdt is NOW, a specific string.
        if isinstance(mdt, str):
            try:
                mdt = MarketDateTime.from_str(mdt)
            except Exception as e:
                raise ValueError(f"Tried to create a MarketDateTime from str \"{mdt}\", encountered Exception:\n\t{str(e)}")
        elif isinstance(mdt, datetime):
            try:
                mdt = MarketDateTime.from_datetime(mdt)
            except Exception as e:
                raise ValueError(f"Tried to create a MarketDateTime from datetime \"{mdt}\", encountered Exception:\n\t{str(e)}")

        #mdt should be a MarketDateTime instance and should have the timezone EAST_TZ (given in constants above, taken from config)
        if (not isinstance(mdt, MarketDateTime)) or (mdt.tzinfo != EAST_TZ):
            raise ValueError("parameter mdt must be a MarketDateTime with eastern timezone (mdt = MarketDateTime(tz=config.EAST_TZ)).")
        return mdt

