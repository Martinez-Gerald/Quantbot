import pandas as pd
import ta
import json
import os

class AdaptiveScalper:
    def __init__(self, state_file="brain_state.json"):
        self.history = []
        self.state_file = state_file
        
        # Default starting values
        self.rsi_buy_threshold = 40
        self.rsi_sell_threshold = 60
        self.win_streak = 0
        self.lose_streak = 0
        
        # Load previous memory if it exists
        self.load_brain()

    def save_brain(self):
        """Saves learned parameters to disk"""
        state = {
            "rsi_buy": self.rsi_buy_threshold,
            "rsi_sell": self.rsi_sell_threshold,
            "wins": self.win_streak,
            "losses": self.lose_streak
        }
        with open(self.state_file, "w") as f:
            json.dump(state, f)
        print("💾 BRAIN SAVED.")

    def load_brain(self):
        """Loads learned parameters from disk"""
        if os.path.exists(self.state_file):
            try:
                with open(self.state_file, "r") as f:
                    state = json.load(f)
                    self.rsi_buy_threshold = state.get("rsi_buy", 30)
                    self.rsi_sell_threshold = state.get("rsi_sell", 70)
                    self.win_streak = state.get("wins", 0)
                    self.lose_streak = state.get("losses", 0)
                print(f"🧠 MEMORY LOADED: Buy<{self.rsi_buy_threshold} | Sell>{self.rsi_sell_threshold}")
            except:
                print("⚠️ MEMORY CORRUPTED. STARTING FRESH.")

    def update_learning(self, last_trade_result):
        if last_trade_result == 'WIN':
            self.win_streak += 1
            self.lose_streak = 0
            # Relax rules slightly to capture more profit
            self.rsi_buy_threshold = min(40, self.rsi_buy_threshold + 1)
            self.rsi_sell_threshold = max(60, self.rsi_sell_threshold - 1)
        
        elif last_trade_result == 'LOSS':
            self.lose_streak += 1
            self.win_streak = 0
            # Tighten rules to stop bleeding
            self.rsi_buy_threshold = max(15, self.rsi_buy_threshold - 2)
            self.rsi_sell_threshold = min(85, self.rsi_sell_threshold + 2)
            
        print(f"🧠 ADAPTED: Buy RSI < {self.rsi_buy_threshold} | Sell RSI > {self.rsi_sell_threshold}")
        self.save_brain() # <--- SAVE AFTER EVERY LESSON

    def analyze(self, price):
        # (Same analysis logic as before...)
        self.history.append(price)
        if len(self.history) > 100: self.history.pop(0)
        if len(self.history) < 20: return "WAITING", 0.0, 0.0

        df = pd.DataFrame(self.history, columns=['close'])
        
        # RSI & Bollinger logic
        df['rsi'] = ta.momentum.rsi(df["close"], window=14)
        indicator_bb = ta.volatility.BollingerBands(close=df["close"], window=20, window_dev=2)
        
        current_rsi = df['rsi'].iloc[-1]
        lower_band = indicator_bb.bollinger_lband().iloc[-1]
        upper_band = indicator_bb.bollinger_hband().iloc[-1]
        
        if price <= lower_band and current_rsi < self.rsi_buy_threshold:
            return "BUY", current_rsi, lower_band
        elif price >= upper_band and current_rsi > self.rsi_sell_threshold:
            return "SELL", current_rsi, upper_band
        else:
            return "HOLD", current_rsi, 0.0