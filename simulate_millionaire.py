# File: simulate_millionaire.py
import random
import statistics

# --- CONFIGURATION ---
STARTING_CAPITAL = 500          # Initial Bankroll
TARGET_WEALTH = 1000000         # The "Retirement" Trigger
MONTHLY_SALARY = 10000          # Living expenses to withdraw in Phase 2

# STRATEGY SETTINGS (Solana Aggressive)
WIN_RATE = 0.60
WIN_PCT = 0.015                 # +1.5%
LOSS_PCT = -0.010               # -1.0%
TRADES_PER_MONTH = 60           # 2-3 trades per day avg

def run_full_simulation():
    balance = STARTING_CAPITAL
    months_passed = 0
    phase = "ACCUMULATION"
    
    # Simulate for 10 years (120 months) total
    for month in range(1, 121):
        months_passed = month
        
        # Determine Risk based on Phase
        if balance < TARGET_WEALTH:
            phase = "ACCUMULATION"
            bet_size_pct = 0.50  # 50% risk for maximum growth
        else:
            phase = "INCOME"
            bet_size_pct = 0.10  # 10% risk to protect the million
            
        # Execute Month's Trading
        for _ in range(TRADES_PER_MONTH):
            bet_amount = balance * bet_size_pct
            if random.random() < WIN_RATE:
                balance += bet_amount * WIN_PCT
            else:
                balance += bet_amount * LOSS_PCT
        
        # Handle Living Expenses (Only in Income Phase)
        if phase == "INCOME":
            balance -= MONTHLY_SALARY
            
        # Safety Check
        if balance <= 0:
            return "FAILED", months_passed, 0

    return "SUCCESS", months_passed, balance

# --- RUN BATCH SIMULATION ---
print(f"--- 🦅 MISSION: THE $500 INDEPENDENCE PLAN ---")
print(f"Phase 1: Grow $500 to $1M (0 Expenses)")
print(f"Phase 2: Withdraw ${MONTHLY_SALARY:,.0f}/mo (Conservative Risk)")

results = []
for _ in range(1000):
    results.append(run_full_simulation())

# Stats calculation
successful_runs = [r for r in results if r[0] == "SUCCESS"]
avg_final_balance = statistics.mean([r[2] for r in successful_runs])

print(f"\n📊 10-YEAR OUTLOOK:")
print(f"✅ Survival Rate: {len(successful_runs)/10}%")
print(f"💰 Avg. Balance after 10 years: ${avg_final_balance:,.2f}")
print(f"💡 (Note: This is after taking ${MONTHLY_SALARY*12:,.0f}/year in salary)")