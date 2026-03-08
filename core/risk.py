class RiskManager:
    def __init__(self, initial_equity):
        self.high_water_mark = initial_equity
        self.current_equity = initial_equity
        self.is_halted = False

    def update(self, new_equity):
        """Updates equity and checks for circuit breakers."""
        self.current_equity = new_equity
        
        # Track peak equity (High Water Mark)
        if new_equity > self.high_water_mark:
            self.high_water_mark = new_equity

        # Calculate Drawdown
        drawdown_pct = (self.high_water_mark - new_equity) / self.high_water_mark
        
        # Circuit Breaker Logic (5% Hard Stop)
        if drawdown_pct >= 0.05:
            self.is_halted = True
            return False, f"🚨 HALT: Max Drawdown Hit ({drawdown_pct*100:.2f}%)"
            
        return True, "Risk Nominal"

    def size_position(self, confidence, bankroll):
        """
        Calculates trade size using Half-Kelly Criterion.
        Input: Confidence (0.0 to 1.0) -> Proxy for Win Probability
        """
        if self.is_halted: 
            return 0.0

        # Simplified Kelly: Size = (Win% - Loss%) / Odds
        # We use 'Confidence' as a proxy for Win Probability
        # Assuming 1:1.5 Risk/Reward ratio for this strategy
        win_prob = confidence 
        risk_reward_ratio = 1.5
        
        kelly_pct = win_prob - ((1 - win_prob) / risk_reward_ratio)
        
        # Safety: Half-Kelly
        size_pct = max(0.0, kelly_pct * 0.5)
        
        # Cap at 10% of account for safety
        final_size_pct = min(size_pct, 0.10)
        
        return bankroll * final_size_pct