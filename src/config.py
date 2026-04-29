"""
Application Configuration
Update this file to change titles, descriptions, symbols, and links.
"""


# --- APP SETTINGS ---
APP_TITLE = "Crypto Market Radar"
APP_ICON = "LEO"
APP_LAYOUT = "wide"
THEME = "quartz"
BG_COLOR = "#1a1a1a"

# --- TIMEZONE SETTING ---
# Global offset from UTC in hours (e.g., 7 for UTC+7, -5 for EST)
TIMEZONE_OFFSET = 7

# --- SIDEBAR & WELCOME ---
SIDEBAR_INFO = "Select a module to proceed"
WELCOME_TITLE = "Crypto Market Radar"
WELCOME_TEXT = """
### Welcome to the Advanced Metrics Dashboard

This application allows you to analyze Binance Perpetual Futures with advanced statistical metrics.

#### Modules:
1. **Data Loader**: Fetch and cache historical market data. 
2. **Market Radar**: Visualize and explore metrics.
3. **Regression**: Analyze predictive power of indicators.
"""

# --- DATA SETTINGS ---
# Symbols that are always fetched
MANDATORY_CRYPTO = ['BTCUSDT', 'ETHUSDT', 'BNBUSDT', 'SOLUSDT', 'BTCDOMUSDT', 'PAXGUSDT', 'XAUUSDT', 'XAGUSDT', 'CLUSDT']
IGNORED_CRYPTO = []

# Benchmark used for Relative Strength and Beta
BENCHMARK_SYMBOL = 'BTCUSDT'

# Default timeframes available in Data Loader
AVAILABLE_INTERVALS = ['1m', '15m', '1h', '4h', '1d', '1w']
DEFAULT_FETCH_INTERVALS = ['1h', '4h', '1d']

# --- EXTERNAL LINKS ---
TRADINGVIEW_URL = "https://www.tradingview.com/chart/"

# --- METRIC LABELS ---
METRIC_LABELS = {
    'volatility': 'Volatility',
    'adf_hist': 'ADF Regime',
    'adf_stat': 'ADF Statistic',
    'fip': 'FIP',
    'count': 'Data Points',
    'ewva': 'EWVA',
    'aroon_osc': 'Aroon Oscillator',
    'rsi_norm': 'RSI (Normalized)',
    'atr_norm': 'Normalized ATR',
    'cmf': 'Chaikin Money Flow',
    'vwap_z': 'VWAP Z-Score',
    'rel_strength_z': 'RS Z-Score',
    'price_zscore': 'Price Z-Score',
    'vam': 'VAM (Vol-Adj Momentum)',
    'skewness': 'Return Skewness',
    'sign_lag1': 'Sign Lag 1',
    'sign_lag2': 'Sign Lag 2',
    'sign_lag3': 'Sign Lag 3',
    'rolling_sign_lag5': 'Rolling Sign (5)',
    'rolling_sign_lag10': 'Rolling Sign (10)',
    'rolling_sign_lag20': 'Rolling Sign (20)',
    'autocorr_1': 'Autocorr (1)',
    'autocorr_5': 'Autocorr (5)',
    'imbalance_bar': 'Imbalance Bar',
    'vol_imbalance': 'Volatility Imbalance',
    'volume_imbalance': 'Volume Imbalance',
    'vol_atr': 'Vol/ATR Ratio',
    'vama': 'VAMA',
    'liquidity_impact': 'Liquidity Impact',
    'vol_rank': 'Volatility Rank',
    'max_drawdown': 'Max Drawdown',
    'avg_drawdown': 'Average Drawdown',
    'breakout_score_v1': 'Breakout Score v1',
    'breakout_score_v2': 'Breakout Score v2',
    'breakout_score_v1_1d': 'Breakout Score v1 (D)',
    'breakout_score_v2_1d': 'Breakout Score v2 (D)',
    'breakout_score_v1_change': 'Breakout Score v1 (Change)',
    'breakout_score_v2_change': 'Breakout Score v2 (Change)',
    'orderbook_imbalance': 'OBook Imbalance',
    'spread': 'Spread',
    'None': 'None'
}

# List of all available numeric metrics for axes
ALL_METRICS = [
    'rel_strength_z',
    'breakout_score_v1', 'breakout_score_v2', 
    'breakout_score_v1_1d', 'breakout_score_v2_1d',
    'breakout_score_v1_change', 'breakout_score_v2_change',
    'price_zscore', 'vam',
    'volatility','vol_imbalance', 'fip', 'ewva', 
    'rsi_norm', 'cmf', 'imbalance_bar', 'volume_imbalance', 'vol_rank',
    'max_drawdown', 'avg_drawdown', 
]

DEFAULT_FEATURES = [
    'rel_strength_z',
    'breakout_score_v1', 'breakout_score_v2',
    'breakout_score_v1_1d', 'breakout_score_v2_1d',
    'breakout_score_v1_change', 'breakout_score_v2_change',
    'price_zscore', 'vam',
    'volatility','vol_imbalance', 'fip', 'ewva', 
    'rsi_norm', 'cmf', 'imbalance_bar', 'volume_imbalance', 'vol_rank',
    'max_drawdown', 'avg_drawdown', 
]
