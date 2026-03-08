# File: main.py
import asyncio
import ccxt.async_support as ccxt
import json
import os
from datetime import datetime
from termcolor import cprint
from dotenv import load_dotenv

# Core Modules
from core.risk import RiskManager
from core.db import init_db, SessionLocal, MarketData, Trade, SystemState
from core.scalper import AdaptiveScalper
from core.notify import send_discord_alert

load_dotenv()

async def main():
    cprint("--- 🦅 QUANT BOT: DUAL-ASSET COMMANDER ($500 START) ---", "magenta")
    
    # 1. Initialize Database
    init_db()
    
    # 2. Setup Exchange
    try:
        with open("cdp_api_key.json", "r") as f:
            keys = json.load(f)
        exchange = ccxt.coinbase({
            'apiKey': keys['name'],        
            'secret': keys['privateKey'],  
            'enableRateLimit': True,
        })
    except Exception as e:
        cprint(f"❌ KEY ERROR: {e}", "red")
        return

    # 3. Connection Test
    try:
        cprint("🔌 Connecting to Coinbase...", "cyan")
        balance = await exchange.fetch_balance()
        usd_balance = balance['total'].get('USD', balance['total'].get('USDC', 0))
        cprint(f"✅ SUCCESS: Connected! USD Balance: ${usd_balance:.2f}", "green")
    except Exception as e:
        cprint(f"❌ AUTH ERROR: {e}", "red")
        await exchange.close()
        return

    # 4. Initialize Brains
    scalpers = {
        'BTC/USD': AdaptiveScalper(),
        'ETH/USD': AdaptiveScalper(),
        'SOL/USD': AdaptiveScalper()  # 👈 Added SOL
    }
    
    # 5. DEFINE WATCHLIST
    watchlist = ['BTC/USD', 'ETH/USD', 'SOL/USD']
    
    # Track positions independently
    positions = {sym: None for sym in watchlist}
    entry_prices = {sym: 0.0 for sym in watchlist}

    try:
        while True:
            db = SessionLocal()
            
            # A. KILL SWITCH CHECK
            state = db.query(SystemState).first()
            if not state:
                state = SystemState(kill_switch=False)
                db.add(state)
                db.commit()

            if state.kill_switch:
                cprint("⛔ HALTED: Kill Switch Active", "red")
                await asyncio.sleep(5)
                db.close()
                continue

            # === CYCLE THROUGH WATCHLIST ===
            for symbol in watchlist:
                
                # B. FETCH MARKET DATA
                try:
                    ticker = await exchange.fetch_ticker(symbol)
                    price = ticker['last']
                    
                    # 👇 NEW ADDITION: HEARTBEAT DISPLAY 👇
                    # This prints the price while it gathers the first 20 candles
                    data_count = len(scalpers[symbol].history)
                    if data_count < 20:
                        print(f"💓 {symbol} | ${price:.2f} | Gathering Data: {data_count+1}/20")
                    # 👆 END ADDITION 👆

                except Exception as e:
                    cprint(f"⚠️ {symbol} Data Error: {e}", "yellow")
                    continue

                # C. ANALYZE
                current_scalper = scalpers[symbol]
                signal, rsi, band_target = current_scalper.analyze(price)
                
                # Log status periodically
                if len(current_scalper.history) > 20:
                    log_msg = f"{symbol}: ${price:.2f} | RSI: {rsi:.2f} | Action: {signal}"
                    if signal != "HOLD":
                        cprint(log_msg, "cyan")

                # D. EXECUTE TRADES
                if positions[symbol] is None:
                    # --- ENTRY LOGIC ---
                    if signal == "BUY":
                        available_cash = float(usd_balance) if usd_balance > 0 else 500.0
                        allocation = available_cash * 0.45
                        size_usd = allocation

                        if size_usd > 10: 
                            msg = f"🚀 **{symbol} BUY** | Price: ${price} | RSI: {rsi:.2f} | Size: ${size_usd:.2f}"
                            cprint(msg, "green", attrs=['bold'])
                            send_discord_alert(msg)
                            
                            db.add(Trade(symbol=symbol, side='BUY', price=price, size=size_usd/price))
                            db.commit()
                            
                            positions[symbol] = 'LONG'
                            entry_prices[symbol] = price

                else:
                    # --- EXIT LOGIC ---
                    entry = entry_prices[symbol]
                    pnl_pct = (price - entry) / entry
                    
                    # CHANGED: 1.5% Profit / 1.0% Loss (Faster turnover)
                    take_profit = 0.015 
                    stop_loss = -0.010

                    if pnl_pct >= take_profit: 
                        msg = f"💰 **{symbol} WIN** | +{pnl_pct*100:.2f}% | Price: ${price}"
                        cprint(msg, "green")
                        send_discord_alert(msg)
                        
                        scalpers[symbol].update_learning('WIN')
                        db.add(Trade(symbol=symbol, side='SELL (WIN)', price=price, size=0, pnl=pnl_pct))
                        db.commit()
                        positions[symbol] = None
                    
                    elif pnl_pct <= stop_loss:
                        msg = f"🛑 **{symbol} LOSS** | {pnl_pct*100:.2f}% | Price: ${price}"
                        cprint(msg, "red")
                        send_discord_alert(msg)
                        
                        scalpers[symbol].update_learning('LOSS')
                        db.add(Trade(symbol=symbol, side='SELL (LOSS)', price=price, size=0, pnl=pnl_pct))
                        db.commit()
                        positions[symbol] = None

                # Record Data for Dashboard
                db.add(MarketData(time=datetime.utcnow(), symbol=symbol, price=price))
                db.commit()
                
                await asyncio.sleep(1)

            db.close()
            await asyncio.sleep(5)

    except KeyboardInterrupt:
        cprint("\n🛑 Bot Stopped by User", "yellow")
    finally:
        await exchange.close()
        cprint("🔌 Connection Closed", "white")

if __name__ == "__main__":
    asyncio.run(main())