import os
import sys
from pathlib import Path

# Add the current directory to the path so we can import src
sys.path.append(str(Path(__file__).parent))

from shiny import App, ui, render, reactive
import pandas as pd
import numpy as np
import faicons as fa

from shinywidgets import output_widget, render_widget
from src.config import APP_TITLE, APP_ICON, WELCOME_TITLE, WELCOME_TEXT, SIDEBAR_INFO, THEME, BG_COLOR, TRADINGVIEW_URL
import requests
import webbrowser

from modules.market_radar import market_radar_ui, market_radar_server
from src.data import DataManager
from src.metrics import MetricsEngine
from src.config import BENCHMARK_SYMBOL
from datetime import datetime, timedelta

# UI definition
app_ui = ui.page_navbar(
    ui.head_content(
        ui.include_css(Path(__file__).parent / "www" / "custom.css"),
        ui.tags.script("""
            document.addEventListener("keydown", function(e) {
                const decomp_n_assets_box = document.querySelector('input[id$="decomp_n_assets"]');
                if (decomp_n_assets_box && document.activeElement === decomp_n_assets_box && e.key === "Enter") {
                    document.activeElement.blur();
                }
            });
            $(document).on('bslib.card.expand', function(event) {
                Shiny.setInputValue('card_expanded', true);
            });
            $(document).on('bslib.card.collapse', function(event) {
                Shiny.setInputValue('card_expanded', false);
            });
        """)
    ),

    ui.nav_panel("MARKET_RADAR", market_radar_ui()),

    ui.nav_spacer(),
    ui.nav_control(
        ui.div(
            ui.div(
                ui.input_selectize(
                    "quick_symbol",
                    None,
                    choices=[],
                    multiple=True,
                    options={"placeholder": "Launch Assets"}
                ),
                class_="flex-grow-1"
            ),
            ui.div(
                ui.input_action_button(
                    "btn_quick_go",
                    fa.icon_svg("paper-plane"),
                    class_="btn-primary btn-sm"
                ),
                class_="flex-shrink-0",
                style="margin-top: -14px;"
            ),
            class_="d-flex align-items-center gap-2"
        )
    ),
    id="main_nav",
    selected="MARKET_RADAR"
)


def server(input, output, session):
    # Shared global state if needed
    global_interval = reactive.Value("1h")
    manager = DataManager()
    engine = MetricsEngine()
    
    @reactive.Effect
    def populate_symbols():
        with ui.Progress(min=0, max=1) as p:
            p.set(0, message="Initializing Market Data...")
            all_syms = manager.get_universe()
            p.set(1, message="Populating Global Selectors...")
            ui.update_selectize("quick_symbol", choices=all_syms, server=True)

    @reactive.Effect
    @reactive.event(input.btn_quick_go)
    def _quick_link():
        symbols = input.quick_symbol()
        if not symbols:
            return
            
        # Get interval from Market Radar module if possible
        try:
            interval = input.radar_interval()
        except:
            interval = "1h"

        # TradingView interval mapping
        tv_intervals = {
            '1m': '1', '3m': '3', '5m': '5', '15m': '15', '30m': '30',
            '1h': '60', '2h': '120', '4h': '240', '6h': '360', '8h': '480', '12h': '720',
            '1d': 'D', '3d': '3D', '1w': 'W'
        }
        tv_int = tv_intervals.get(interval, '60')

        if isinstance(symbols, (list, tuple)):
            for sym in symbols:
                # Remove 'USDT' for clean Binance symbol if needed, or keep as is
                # TradingView expects BINANCE:BTCUSDT
                url = f"{TRADINGVIEW_URL}?symbol=BINANCE:{sym}&interval={tv_int}"
                webbrowser.open(url)
        
        ui.update_selectize("quick_symbol", selected=[])

    market_radar_server(input, output, session, global_interval)

app = App(app_ui, server)
