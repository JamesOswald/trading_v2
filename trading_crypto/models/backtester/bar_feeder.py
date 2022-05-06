class BarFeeder():
    """
    Feeds a set of already created bar to the strategy
    """
    def __init__(self, symbol, timestamp_bar_map):
        self.symbol = symbol
        self.timestamp_bar_map = timestamp_bar_map
    
    def __repr__(self):
        return "Bar Feeder<{}>".format(self.symbol)
    
    