import os
from dotenv import load_dotenv

load_dotenv()
class Config:
    #Toggle this to False when you are ready to lose real money
    PAPER_TRADING_MODE = True
    
    #Database
    DB_URL = "postgresql://postgres:password123@localhost:5432/trading_bot"
    
    # Risk Limits
    MAX_DRAWDOWN_PCT = 0.05 # 5% hard stop
    KELLY_FRACTION = 0.5 # Half-Kelly