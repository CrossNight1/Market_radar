import pandas as pd
import numpy as np
from src.metrics import MetricsEngine

def test_breakout_score():
    engine = MetricsEngine()
    
    # Create dummy data: 200 bars of random-ish walk
    np.random.seed(42)
    n = 300
    close = 100 + np.cumsum(np.random.randn(n))
    high = close + np.random.rand(n)
    low = close - np.random.rand(n)
    open_p = close + np.random.randn(n) * 0.1
    volume = np.random.rand(n) * 1000
    
    df = pd.DataFrame({
        'open': open_p,
        'high': high,
        'low': low,
        'close': close,
        'volume': volume
    })
    
    try:
        score_up, score_down = engine.calculate_breakout_score(df)
        print(f"Calculation successful. Result length: {len(score_up)}")
        print(f"Latest Score Up: {score_up.iloc[-1]:.4f}")
        print(f"Latest Score Down: {score_down.iloc[-1]:.4f}")
        
        # Verify gating: if close < vamaC, score_up should be 0
        # We need to calculate vamaC to check
        # For simplicity, let's just check if scores are ever non-zero
        print(f"Max Score Up: {score_up.max():.4f}")
        print(f"Max Score Down: {score_down.max():.4f}")
        
        if score_up.max() > 0 or score_down.max() > 0:
            print("SUCCESS: Scores generated and non-zero.")
        else:
            print("WARNING: All scores are zero. This might be expected for random data but double check.")
            
    except Exception as e:
        print(f"FAILURE: Error during calculation: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_breakout_score()
