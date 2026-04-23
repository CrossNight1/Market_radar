import pandas as pd
import numpy as np
from src.metrics import MetricsEngine

def test_breakout_score_1d():
    engine = MetricsEngine()
    
    # Create dummy data for current interval (e.g., 1h)
    n = 300
    df_1h = pd.DataFrame({
        'open': 100 + np.random.randn(n),
        'high': 101 + np.random.randn(n),
        'low': 99 + np.random.randn(n),
        'close': 100 + np.random.randn(n),
        'volume': np.random.rand(n) * 1000,
        'open_time': pd.date_range(start='2024-01-01', periods=n, freq='h')
    })
    
    # Create dummy data for daily interval
    df_1d = pd.DataFrame({
        'open': 100 + np.random.randn(n),
        'high': 101 + np.random.randn(n),
        'low': 99 + np.random.randn(n),
        'close': 100 + np.random.randn(n),
        'volume': np.random.rand(n) * 1000,
        'open_time': pd.date_range(start='2023-01-01', periods=n, freq='D')
    })
    
    try:
        # Compute metrics with daily data
        res_df = engine.compute_all_metrics(
            {'TEST': df_1h}, 
            interval='1h',
            daily_prices={'TEST': df_1d}
        )
        
        print(f"Calculation successful. Result row count: {len(res_df)}")
        if 'breakout_score_1d' in res_df.columns:
            val = res_df.iloc[0]['breakout_score_1d']
            print(f"Breakout Score (1D): {val:.4f}")
            print("SUCCESS: breakout_score_1d found in results.")
        else:
            print("FAILURE: breakout_score_1d NOT found in results.")
            
    except Exception as e:
        print(f"FAILURE: Error during calculation: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_breakout_score_1d()
