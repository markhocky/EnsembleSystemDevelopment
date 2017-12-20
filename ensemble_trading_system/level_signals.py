

from pandas import Panel, DataFrame

from system.interfaces import SignalElement
from data_types.signals import Signal


class Crossover(SignalElement):
    '''
    The Crossover signal compares two indicators (fast and slow) to determine whether
    the prevailing trend is 'Up' (fast > slow) or 'Down' (fast <= slow).
    '''
    def __init__(self, slow, fast):
        self.fast = fast
        self.slow = slow

    @property
    def name(self):
        return "x".join([self.fast.name, self.slow.name])

    def execute(self, strategy):
        prices = strategy.get_indicator_prices()
        fast_ema = self.fast(prices)
        slow_ema = self.slow(prices)

        ind_data = strategy.get_empty_dataframe(fill_data = 'Down')
        ind_data[fast_ema > slow_ema] = 'Up'

        return Signal(ind_data, ['Up', 'Down'], Panel.from_dict({'Fast':fast_ema, 'Slow':slow_ema}))
    
    def update_param(self, new_params):
        self.slow.update_param(max(new_params))
        self.fast.update_param(min(new_params))


class TripleCrossover(SignalElement):
    '''
    The Triple Crossover signal is similar to the Crossover except it uses three indicators (fast, mid and slow).
    The prevailing trend is 'Up' when (fast > mid) and (mid > slow), and 'Down' otherwise.
    '''
    def __init__(self, slow, mid, fast):
        self.fast = fast
        self.mid = mid
        self.slow = slow

    @property
    def name(self):
        return "x".join([self.fast.name, self.mid.name, self.slow.name])
        
    def execute(self, strategy):
        prices = strategy.get_indicator_prices()
        fast_ema = self.fast(prices)
        mid_ema = self.mid(prices)
        slow_ema = self.slow(prices)
        levels = (fast_ema > mid_ema) & (mid_ema > slow_ema)

        ind_data = strategy.get_empty_dataframe(fill_data = 'Down')
        ind_data[levels] = 'Up'
        return Signal(ind_data, ['Up', 'Down'], Panel.from_dict({'Fast':fast_ema, 'Mid':mid_ema, 'Slow':slow_ema}))
    
    def update_param(self, new_params):
        pars = list(new_params)
        pars.sort()
        self.fast = pars[0]
        self.mid = pars[1]
        self.slow = pars[2]


class Breakout(SignalElement):

    def __init__(self, breakout_measure):
        self.breakout = breakout_measure
        self.name = self.breakout.name

    def execute(self, strategy):
        prices = strategy.get_indicator_prices()
        breakout = self.breakout(prices)
        high = breakout["high"]
        low = breakout["low"]

        ind_data = strategy.get_empty_dataframe()
        ind_data[prices == high] = 'Up'
        ind_data[prices == low] = 'Down'
        ind_data.ffill()

        return Signal(ind_data, ['Up', 'Down'], breakout)
    
    def update_param(self, new_params):
        self.breakout.update_param(max(new_params))


# TODO ValueWeightedEMA is not complete
class ValueWeightedEMA(SignalElement):

    def __init__(self, values, fast, slow):
        self.values = values
        self.fast = fast
        self.slow = slow

    @property
    def name(self):
        return ".".join([self.values.name, "Wtd", self.fast.name, self.slow.name])

    def execute(self, strategy):
        prices = strategy.get_indicator_prices()
        value_ratio = DataFrame(prices)
        value_ratio[:] = None
        for col in self.values:
            value_ratio[col] = self.values[col]
        value_ratio.fillna(method = 'ffill')
        value_ratio = value_ratio / prices

    def update_param(self, new_params):
        pass


