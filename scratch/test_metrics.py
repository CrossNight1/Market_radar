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
        score_up_dist, score_down_dist, score_up_break, score_down_break = engine.calculate_breakout_score(df)
        print(f"Calculation successful. Result length: {len(score_up_dist)}")
        print(f"Max Score Up (Dist): {score_up_dist.max():.4f}")
        print(f"Max Score Down (Dist): {score_down_dist.max():.4f}")
        print(f"Max Score Up (Break): {score_up_break.max():.4f}")
        print(f"Max Score Down (Break): {score_down_break.max():.4f}")
        
        if score_up_dist.max() > 0 or score_up_break.max() > 0:
            print("SUCCESS: Scores generated and non-zero.")
        else:
            print("WARNING: All scores are zero. This might be expected for random data but double check.")
            
    except Exception as e:
        print(f"FAILURE: Error during calculation: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_breakout_score()
