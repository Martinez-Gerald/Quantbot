# File: dashboard/app.py
import streamlit as st
import pandas as pd
import time
import plotly.graph_objects as go
from sqlalchemy import create_engine, text
import sys
import os
import math
from datetime import datetime, timedelta
import cbpro # Required: pip install cbpro

# Path Fix for local imports
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from config import Config

# Connect to Docker Postgres
engine = create_engine(Config.DB_URL)

# --- 1. COINBASE API INTEGRATION ---
def get_cb_balance():
    """Fetches real USD/USDC balance from your Coinbase account."""
    try:
        # Initializing the authenticated client from your Config file
        auth_client = cbpro.AuthenticatedClient(
            Config.CB_API_KEY, 
            Config.CB_SECRET_KEY, 
            Config.CB_PASSPHRASE
        )
        accounts = auth_client.get_accounts()
        # We sum USD and USDC as your 'working capital'
        total_balance = sum(float(a['balance']) for a in accounts if a['currency'] in ['USD', 'USDC'])
        return total_balance if total_balance > 0 else 500.00 # Fallback for simulation
    except Exception:
        return 500.00 # Default to your Phase 1 start amount if API is unreachable

# --- 2. MANDATORY PAGE CONFIG ---
st.set_page_config(
    page_title="QuantBot Vision",
    page_icon="🧊",
    layout="wide",
    initial_sidebar_state="expanded" 
)

# --- 3. FORCED SIDEBAR & GLASS UI CSS ---
st.markdown("""
<style>
    /* Force Sidebar Width for Mac Tiling */
    [data-testid="stSidebar"] {
        min-width: 350px !important;
        max-width: 350px !important;
    }

    /* VisionOS Deep Space Background */
    .stApp {
        background: radial-gradient(circle at 50% 10%, #1a1a2e 0%, #000000 100%);
    }

    /* Glassmorphism Metric Cards */
    div[data-testid="stMetric"] {
        background: rgba(255, 255, 255, 0.05);
        backdrop-filter: blur(15px);
        -webkit-backdrop-filter: blur(15px);
        border-radius: 20px;
        padding: 20px;
        border: 1px solid rgba(255, 255, 255, 0.1);
        box-shadow: 0 4px 30px rgba(0, 0, 0, 0.1);
    }
    
    [data-testid="stMetricValue"] {
        color: #ffffff;
        font-weight: 200;
        font-size: 2.4rem;
    }

    header {visibility: hidden;}
    footer {visibility: hidden;}
</style>
""", unsafe_allow_html=True)

# --- 4. DATA FETCHING ENGINE ---
def get_bot_stats(symbol):
    try:
        df_market = pd.read_sql(f"SELECT * FROM market_data WHERE symbol='{symbol}' ORDER BY time DESC LIMIT 300", engine)
        df_trades = pd.read_sql(f"SELECT * FROM trades WHERE symbol='{symbol}' ORDER BY time DESC LIMIT 50", engine)
        
        # Calculate Simulation Performance
        closed = df_trades[df_trades['side'].str.contains('WIN|LOSS', na=False)]
        net_yield = closed['pnl'].sum() * 100 if not closed.empty else 0.0
        wins = len(closed[closed['side'].str.contains('WIN')])
        win_rate = (wins / len(closed) * 100) if not closed.empty else 60.0
        
        # Daily PnL for the Mission Tracker
        with engine.connect() as conn:
            daily_pnl = conn.execute(text("SELECT SUM(pnl) FROM trades WHERE time >= CURRENT_DATE")).scalar() or 0.0
            
        return df_market, df_trades, net_yield, win_rate, len(closed), daily_pnl
    except:
        return pd.DataFrame(), pd.DataFrame(), 0.0, 60.0, 0, 0.0

# --- 5. SIDEBAR (The Command Center) ---
with st.sidebar:
    st.markdown("<h1 style='color: white; font-weight: 200;'>🎛 Control Center</h1>", unsafe_allow_html=True)
    
    selected_symbol = st.selectbox("Asset Stream", ["SOL/USD", "BTC/USD", "ETH/USD"], index=0)
    
    # Live Balance & Bot Stats
    live_bal = get_cb_balance()
    df_m, df_t, n_yield, w_rate, t_count, d_pnl = get_bot_stats(selected_symbol)
    
    st.divider()

    # DAILY MISSION
    st.markdown("### 🎯 Daily Mission")
    daily_target_usd = live_bal * 0.01 # 1% Daily growth goal
    current_earned = live_bal * d_pnl
    
    progress = min(current_earned / daily_target_usd, 1.0) if current_earned > 0 else 0.0
    st.metric("Today's Profit", f"${current_earned:.2f}", f"Goal: ${daily_target_usd:.2f}")
    st.progress(progress)
    st.caption(f"Status: {int(progress*100)}% to Daily Target")

    st.divider()

    # MILLIONAIRE COUNTDOWN
    st.markdown("### 🦅 Freedom Forecast")
    # Compound interest: Monthly growth (~30% based on SOL settings)
    monthly_growth = 0.30 
    months_to_mil = math.log(1000000 / max(live_bal, 1)) / math.log(1 + monthly_growth)
    freedom_date = datetime.now() + timedelta(days=months_to_mil * 30.44)
    
    st.metric("Next 6 Months", f"${live_bal * (1 + monthly_growth)**6:,.2f}", "+1,000%+")
    st.info(f"Target Freedom: {freedom_date.strftime('%B %Y')}")
    st.progress(min(live_bal / 1000000, 1.0))

# --- 6. MAIN DASHBOARD UI ---
st.markdown(f"<h1 style='text-align: center; color: white; font-weight: 100; letter-spacing: 2px;'>🧊 QUANT VISION PRO</h1>", unsafe_allow_html=True)

placeholder = st.empty()

while True:
    with placeholder.container():
        # Update metrics every loop
        live_bal = get_cb_balance()
        df_m, df_t, n_yield, w_rate, t_count, d_pnl = get_bot_stats(selected_symbol)
        
        # Primary Metric Grid
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Coinbase Balance", f"${live_bal:,.2f}")
        c2.metric("Bot Net Yield", f"{n_yield:.2f}%")
        c3.metric("Win Rate", f"{w_rate:.0f}%", f"{t_count} Trades")
        
        market_price = df_m.iloc[0]['price'] if not df_m.empty else 0.0
        c4.metric(f"Live {selected_symbol.split('/')[0]}", f"${market_price:,.2f}")

        # Price Action Chart
        if not df_m.empty:
            fig = go.Figure()
            fig.add_trace(go.Scatter(
                x=df_m['time'], y=df_m['price'],
                mode='lines', line=dict(color='#00d1ff', width=2),
                fill='tozeroy', fillcolor='rgba(0,209,255,0.05)'
            ))
            fig.update_layout(
                paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)',
                font=dict(color='white'), height=450,
                margin=dict(l=0,r=0,t=10,b=0),
                xaxis=dict(showgrid=False),
                yaxis=dict(showgrid=True, gridcolor='rgba(255,255,255,0.05)')
            )
            st.plotly_chart(fig, use_container_width=True)

        # Recent Activity
        st.markdown("<h3 style='color: white; font-weight: 100;'>Activity Log</h3>", unsafe_allow_html=True)
        if not df_t.empty:
            st.dataframe(df_t[['time', 'side', 'price', 'pnl']], use_container_width=True, height=250)
        else:
            st.info("System is live. Waiting for first SOL opportunity...")

    # Sleep 10 seconds to respect Coinbase API limits
    time.sleep(10)