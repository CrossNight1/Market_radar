# Deployment Guide

This guide explains how to deploy the **Crypto Market Radar** on a new machine or a remote server (e.g., AWS, DigitalOcean, or a dedicated Linux machine).

## 1. System Setup

Ensure your system has Python 3.9 or newer installed.

### Linux (Ubuntu/Debian)
```bash
sudo apt update
sudo apt install python3-venv python3-pip git screen -y
```

### macOS
```bash
brew install python screen
```

## 2. Application Setup

### Clone and Environment
```bash
git clone <repository-url> market_radar
cd market_radar

python3 -m venv .venv
source .venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
```

## 3. Persistent Deployment (Screen)

To keep the application running after you close your terminal session, use `screen`.

### Start the session
```bash
screen -S market_radar
```

### Run the app
Inside the screen session, activate the venv and start the server:
```bash
source .venv/bin/activate
shiny run --host 0.0.0.0 --port 8000 app.py
```

### Detach and Exit
1. Press `Ctrl + A`, then `D` to detach. The app is now running in the background.
2. You can safely close your terminal.

### Re-attach later
```bash
screen -r market_radar
```

## 4. Production Optimization

### External Access
If you are running on a remote VPS, ensure port `8000` is open in your firewall (Security Groups/ufw).

### Network Performance
The `DataManager` uses parallel fetching. If you experience network timeouts on smaller machines, you can adjust the `max_workers` in:
- `modules/market_radar.py` (within `_handle_radar_sync`)
- `src/data.py` (within `DataManager.sync_all`)

## 5. Maintenance

### Updating the App
```bash
git pull
source .venv/bin/activate
pip install -r requirements.txt
# Restart the screen session or the app inside it
```

### Clearing Cache
If you encounter data corruption or want to force a fresh sync:
```bash
rm -rf data_cache/*.parquet
```

---

## 🔒 Security Note
This application is currently designed for internal use. If you plan to expose it to the public internet, it is highly recommended to put it behind a reverse proxy like **Nginx** with **Basic Auth** or **SSL** certificates.
