
"""
interfaces contains the basic structures for strategy building blocks. Most of the classes in this module
are not intended to be used directly, but to be inherited from for customised functionality.
The interfaces are broken into two broad categories:
    1. The interfaces for data structures (e.g. results of calculations) which predominately handle the 
       correct alignment in time with other calculated data.
    2. The interfaces for calculation methods, which can be thought of to be the mappings between data 
       types. These generally will need to be callable, and will accept a strategy as input (for access 
       to the contained data).
"""
from copy import copy, deepcopy


# DATA CONTAINER TYPES
class DataElement:
    '''
    DataElements represent the data objects used by Strategy.
    Each DataElement is assumed to have a (DataFrame) field called data.
    DataElements also control the appropriate lagging of data to align with other calculation periods.
    When lagged the DataElement returns a copy of itself, and the current applied lag.
    Calculation timing represents the timing for when the data is calculated and may be a single value, 
    e.g. ["decision", "entry", "exit", "open", "close"], or a twin value which represents the calculations 
    occur over some span of time, e.g. for returns which have timing ["entry", "exit"]
    '''
    def shift(self, lag):
        lagged = self.copy()
        lagged.data = self.data.copy() # Note: deepcopy doesn't seem to copy the dataframe properly; hence this line.
        lagged.data = lagged.data.shift(lag)
        lagged.lag += lag
        return lagged

    def at(self, timing):
        '''
        'at' returns a lagged version of the data appropriate for the timing.
        Timing may be one of: ["decision", "entry", "exit", "open", "close"]
        '''
        lag = self.get_lag(timing)
        return self.shift(lag)

    def align_with(self, other):
        '''
        'align_with' returns a lagged version of the data so that it is aligned with the 
        timing of the supplied other data object. This ensures that this data will be available at the 
        time creation of the other data object would have started.
        The logic for the overall lag calculated in align_with is as follows:
        - total lag = alignment lag + other lag
            - alignment lag = lag between this data calc end to the other data calc start
            - other lag = the lag already applied to the other data.
        '''
        alignment_lag = self.get_lag(other.calculation_timing[0])
        total_lag = alignment_lag + other.lag
        return self.shift(total_lag)

    def get_lag(self, target_timing):
        '''
        Calculate the lag between the completion of calculating this data object and the requested timing.
        '''
        return self.indexer.get_lag(self.calculation_timing[-1], target_timing)

    @property
    def index(self):
        return self.data.index

    @property
    def tickers(self):
        return self.data.columns

    def __getitem__(self, key):
        return self.data[key]

    def copy(self):
        return deepcopy(self)


class Indexer:
    
    def __init__(self, trade_timing, ind_timing):
        if trade_timing not in ["OO", "CC"]:
            raise ValueError("Trade timing must be one of: 'OO', 'CC'.")
        self.trade_timing = trade_timing
        if ind_timing not in ["O", "C"]:
            raise ValueError("Ind_timing must be one of: 'O', 'C'")
        self.ind_timing = ind_timing
        self.timing_map = {"decision" : self.ind_timing, 
                           "entry" : self.trade_timing[0], 
                           "exit" : self.trade_timing[-1], 
                           "open" : "O", 
                           "close" : "C"}


    def get_lag(self, start, end):
        start = self.convert_timing(start)
        end = self.convert_timing(end)
        if "OC" in start + end:
            lag = 0
        else:
            lag = 1
        return lag

    def convert_timing(self, timing):
        timing = timing.lower()
        if timing not in self.timing_map.keys():
            raise ValueError("Timing must be one of: " + ",".join(self.timing_map.keys()))
        return self.timing_map[timing]
    
    def market_returns(self, market):
        timing_map = {"O":"open", "C":"close"}
        if self.trade_timing == "OC":
            lag = 0
        else:
            lag = 1
        trade_open = getattr(market, timing_map[self.trade_timing[0]])
        trade_close = getattr(market, timing_map[self.trade_timing[1]])
        return (trade_open / trade_close.shift(lag)) - 1



# CALCULATION TYPES
class StrategyElement:
    '''
    The StrategyElement class provides the basic interface for those objects which
    perform calculations based on the strategy data. e.g. to create signals.
    It defines the base functionality required, as well as handling the details of
    assigning the indexer and lag values.
    '''
    @property
    def ID(self): 
        return id(self)
        
    def __call__(self, strategy):
        result = self.get_result(strategy)
        if not self.created(result):
            result = self.execute(strategy)
            result.creator = self.ID
            result.indexer = strategy.indexer
            result.calculation_timing = self.calculation_timing
            result.lag = self.starting_lag()
        return result

    
    def execute(self, strategy):
        raise NotImplementedError("Strategy Element must define 'execute'")
    
    def created(self, result):
        return result is not None and result.creator == self.ID
    
    def get_result(self, strategy):
        raise NotImplementedError("Strategy Element must define 'get_child'")

    def starting_lag(self):
        return 0
    

class SignalElement(StrategyElement):

    def get_result(self, strategy):
        return strategy.signal

    @property
    def calculation_timing(self):
        return ["decision"]

    
class PositionRuleElement(StrategyElement):
    
    def get_result(self, strategy):
        return strategy.positions

    @property
    def calculation_timing(self):
        return ["entry"]


class FilterInterface:

    def __call__(self, strategy):
        return strategy.trades.find(self.accepted_trade)

    def accepted_trade(self, trade):
        '''
        Each filter must implement a method accepted_trade which accepts a trade object
        and returns a boolean to determine if the trade should be kept.
        '''
        raise NotImplementedError("Filter must implement 'accepted_trade' method")

    def plot(self, ticker, start, end, ax):
        raise NotImplementedError("Filter must implement 'plot' method")

