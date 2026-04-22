# Crypto Market Radar PRO

An advanced statistical analysis dashboard for Binance Perpetual Futures. This application provides real-time market screening using high-performance metrics, volatility analysis, and interactive visualizations.

![Market Radar Screenshot](https://via.placeholder.com/800x450?text=Market+Radar+Dashboard)

## 🚀 Key Features

- **Real-Time Market Radar**: Multi-dimensional scatter plots (X, Y, Z axes) for cross-asset analysis.
- **Advanced Metrics Engine**:
    - **Relative Strength (Z)**: Measures asset performance relative to BTC.
    - **Breakout Score**: Identifying potential trend shifts using volatility-adjusted momentum.
    - **Standardized Z-Scores**: Price, VWAP, and Volatility standardized for cross-asset comparison.
    - **Market Regimes**: ADF Statistic and Return Skewness for identifying trending vs. mean-reverting phases.
- **Interactive Data Table**: Searchable and filterable grid of all calculated metrics.
- **Quick Asset Launcher**: One-click deep-link to TradingView charts with synchronized symbols and intervals.
- **High-Performance Backend**: Parallel metric calculation using `ThreadPoolExecutor` and optimized caching with Parquet.

## 🛠 Tech Stack

- **Frontend**: [Shiny for Python](https://shiny.posit.co/py/)
- **Visualizations**: [Plotly](https://plotly.com/python/)
- **Data Analysis**: Pandas, NumPy, SciPy, Statsmodels
- **Data Caching**: Parquet (PyArrow / FastParquet)

## 🚦 Quick Start

### 1. Prerequisites
- Python 3.9+
- Git

### 2. Installation
```bash
# Clone the repository
git clone <repository-url>
cd market_radar

# Create and activate virtual environment
python3 -m venv .venv
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### 3. Run the Application
```bash
shiny run --reload app.py
```

## ⚙️ Configuration

All major settings are located in `src/config.py`:
- `MANDATORY_CRYPTO`: Assets that are always prioritized in sync.
- `BENCHMARK_SYMBOL`: The base asset for Relative Strength (Default: BTCUSDT).
- `ALL_METRICS`: Control which columns appear in the dashboard.
- `TRADINGVIEW_URL`: The base URL for the chart launcher.

---

## 📖 Detailed Deployment Guide
For instructions on deploying to a remote server or setting up persistent background execution, see [DEPLOYMENT.md](DEPLOYMENT.md).
