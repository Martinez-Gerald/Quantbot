# File: core/db.py
from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime, Boolean, text
from sqlalchemy.orm import declarative_base, sessionmaker
from datetime import datetime
from config import Config

# Connect to the local Docker Database
engine = create_engine(Config.DB_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# --- TABLE DEFINITIONS ---

class MarketData(Base):
    """Stores real-time price ticks for charting"""
    __tablename__ = 'market_data'
    time = Column(DateTime, primary_key=True, default=datetime.utcnow)
    symbol = Column(String, primary_key=True)
    price = Column(Float)
    
class Trade(Base):
    """Stores your trade history"""
    __tablename__ = 'trades'
    id = Column(Integer, primary_key=True, autoincrement=True)
    time = Column(DateTime, default=datetime.utcnow)
    symbol = Column(String)
    side = Column(String) # BUY or SELL
    price = Column(Float)
    size = Column(Float)
    pnl = Column(Float, default=0.0)

class SystemState(Base):
    """Stores global controls like the Kill Switch"""
    __tablename__ = 'system_state'
    id = Column(Integer, primary_key=True)
    kill_switch = Column(Boolean, default=False)
    market_regime = Column(String, default="NEUTRAL")

# --- HELPER FUNCTIONS ---

def init_db():
    """Creates the tables if they don't exist"""
    try:
        Base.metadata.create_all(bind=engine)
        
        # Initialize default System State
        db = SessionLocal()
        if not db.query(SystemState).first():
            print("⚙️ Initializing System State Table...")
            db.add(SystemState(kill_switch=False, market_regime="NEUTRAL"))
            db.commit()
        db.close()
        print("✅ Database Connected & Initialized")
    except Exception as e:
        print(f"❌ Database Connection Failed: {e}")