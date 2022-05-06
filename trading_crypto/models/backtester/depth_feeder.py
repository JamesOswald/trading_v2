class DepthFeeder():
    """
    Feeds a set of already created depths to the strategy
    """
    def __init__(self, symbol, timestamp_depth_map):
        self.symbol = symbol
        self.timestamp_depth_map = timestamp_depth_map