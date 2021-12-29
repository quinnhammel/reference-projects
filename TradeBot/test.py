import MarketDateTime
import PriceMoment
import config

#quick test of functionality of MarketDateTime and PriceMoment
def quick_test_mdt_pm():
  x = MarketDateTime.now()
  y = MarketDateTime.from_str(str(x))
  print(y.tzinfo == config.EAST_TZ)
  print(x == y)
  print(str(x) == str(y))

  p0 = PriceMoment(x, 1.0, 2.4, 5)
  s0 = str(p0)

  print(s0)

  p1 = PriceMoment.from_str(s0)
  s1 = str(p1)

  print(s1)


  print(s0 == s1)