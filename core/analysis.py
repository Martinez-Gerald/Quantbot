# File: core/analysis.py
import pandas as pd
#import pandas_ta as ta  # We need to install this library first!

class MarketAnalyzer:
    def __init__(self):
        self.history = []

    def update_price(self, price):
        """Adds new price to history and trims to keep it fast."""
        self.history.append(price)
        if len(self.history) > 100:
            self.history.pop(0) # Remove oldest price

    def get_regime(self):
        """
        Calculates SMA (Simple Moving Average) to determine regime.
        """
        if len(self.history) < 20:
            return "WAITING_DATA"

        # Convert list to Pandas Series for easy math
        series = pd.Series(self.history)

        # Calculate Indicators
        sma_short = series.rolling(window=5).mean().iloc[-1]
        sma_long = series.rolling(window=15).mean().iloc[-1]
        current_price = self.history[-1]

        # Logic
        if sma_short > sma_long:
            return "BULLISH"
        elif sma_short < sma_long:
            return "BEARISH"
        else:
            return "SIDEWAYS"