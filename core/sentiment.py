# File: core/sentiment.py
from textblob import TextBlob
import random

class SentimentEngine:
    def __init__(self):
        # In a real bot, we would fetch these from an API like CryptoPanic
        self.mock_headlines = [
            "Bitcoin hits new all time high!",
            "Regulatory concerns cause market dip.",
            "Tech giants investing heavily in crypto.",
            "Network congestion slowing down transactions.",
            "Market looks bullish as adoption grows.",
            "Investors are fearful of upcoming interest rates."
        ]

    def analyze(self):
        """
        Returns a sentiment score between -1.0 (Negative) and 1.0 (Positive).
        """
        # 1. Pick a random headline (Simulating a new news drop)
        headline = random.choice(self.mock_headlines)
        
        # 2. Use AI (TextBlob) to analyze the language
        analysis = TextBlob(headline)
        score = analysis.sentiment.polarity
        
        return headline, score