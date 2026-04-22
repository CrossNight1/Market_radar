from shiny import ui, render, reactive
import faicons as fa
from shinywidgets import output_widget, render_widget
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from src.data import DataManager
from src.metrics import MetricsEngine
from src.config import METRIC_LABELS, BENCHMARK_SYMBOL, TRADINGVIEW_URL, ALL_METRICS, AVAILABLE_INTERVALS, MANDATORY_CRYPTO, IGNORED_CRYPTO
from src.logger import logger
from concurrent.futures import ThreadPoolExecutor, as_completed
from scipy import stats
import requests
import time

def market_radar_ui():
    return ui.layout_sidebar(
        ui.sidebar(

            ui.h5("Market Filters"),

            ui.input_action_button(
                "btn_calc_snapshot",
                "Load Data",
                class_="btn-primary w-100 mb-2"
            ),
            ui.input_selectize(
                "focus_symbol",
                "Focus Symbol",
                options={"placeholder": "Select a symbol"},
                choices=[],
                multiple=False
            ),

            ui.input_select(
                "radar_interval",
                "Interval",
                selected="1h",
                choices=AVAILABLE_INTERVALS
            ),

            ui.input_numeric(
                "filter_window",
                "Window Size",
                value=40,
                min=5,
                max=500,
                step=5
            ),

            ui.hr(class_="mt-2 mb-2"),

            # ----- AXES (each own row) -----
            ui.input_select(
                "x_axis",
                "X Axis",
                choices={m: METRIC_LABELS.get(m, m) for m in ALL_METRICS},
                selected='rel_strength_z'
            ),

            ui.input_select(
                "y_axis",
                "Y Axis",
                choices={m: METRIC_LABELS.get(m, m) for m in ALL_METRICS},
                selected='breakout_score'
            ),

            ui.input_select(
                "z_axis",
                "Z Axis",
                choices={"None": "None", **{m: METRIC_LABELS.get(m, m) for m in ALL_METRICS}},
                selected='volatility'
            ),

            # ----- LOG SCALE (single row) -----
            ui.layout_columns(
                ui.input_checkbox("x_log", "Log X"),
                ui.input_checkbox("y_log", "Log Y"),
                # ui.input_checkbox("z_log", "Log Z"),
                col_widths=[5, 5]
            ),

            ui.hr(class_="mt-2 mb-2"),
            ui.input_switch(
                "drop_zeros",
                "Exclude Zero Metrics",
                value=False
            ),
            ui.input_switch(
                "show_regression",
                "Show Regression Line",
                value=True
            ),   

            ui.hr(class_="mt-2 mb-2"),              
            ui.input_text(
                "n_assets_radar",
                "Top Volume",
                value="50",
                placeholder="e.g. 20",
                update_on="blur"
            ),
            ui.input_selectize(
                "radar_symbols",
                "Select Symbols",
                choices=[],
                selected=[],
                multiple=True
            )
        ),
        ui.div(
            # Hidden markers to ensure reactive outputs are transmitted
            ui.div(ui.output_text("snapshot_ready"), class_="d-none"),
            
            ui.panel_conditional(
                "input.btn_calc_snapshot == 0",
                ui.div(ui.h4("Click 'Load Data' to see data"), class_="text-center mt-5")
            ),
            ui.panel_conditional(
                "input.btn_calc_snapshot > 0",
                ui.div(
                    ui.card(
                        ui.card_header("Market Radar Snapshot"),
                        output_widget("snapshot_chart"),
                        full_screen=True
                    ),
                    ui.card(
                        ui.card_header("Data Table"),
                        ui.output_data_frame("snapshot_table")
                    )
                )
            )
        )
    )

def market_radar_server(input, output, session, global_interval):
    manager = DataManager()
    engine = MetricsEngine()
    
    snapshot_data = reactive.Value(pd.DataFrame())
    selected_symbol_data = reactive.Value(None)
    
    # Track selected symbols for snapshot
    selected_symbols_radar = reactive.Value(set())

    logger.log("Market Radar", "INFO", "Server initialized")

    @reactive.effect
    @reactive.event(input.btn_calc_snapshot)
    def _initialize_symbols():
        # Only initialize with mandatory if we don't have symbols yet
        if not selected_symbols_radar.get():
            try:
                n = int(input.n_assets_radar() or 20)
                syms = manager.fetcher.get_top_volume_symbols(top_n=n)
            except Exception as e:
                logger.log("Market Radar", "ERROR", f"Initial symbol sync failed: {e}")
                syms = []
            
            new_syms = set(MANDATORY_CRYPTO).union(syms)
            new_syms = {s for s in new_syms if s not in IGNORED_CRYPTO}
            selected_symbols_radar.set(new_syms)

    @reactive.effect
    @reactive.event(input.n_assets_radar)
    def _update_radar_symbols_list():
        try:
            n = int(input.n_assets_radar() or 20)
            try:
                syms = manager.fetcher.get_top_volume_symbols(top_n=n)
            except Exception as e:
                logger.log("Market Radar", "ERROR", f"Radar volume filter failed: {e}")
                syms = []
            
            new_syms = set(MANDATORY_CRYPTO).union(syms)
            # Remove ignored symbols
            new_syms = {s for s in new_syms if s not in IGNORED_CRYPTO}
            
            # This triggers the effect above to update selected_symbols_radar
            ui.update_text("n_assets_radar", value=str(n)) 
            selected_symbols_radar.set(new_syms)
            
            all_syms = manager.get_universe()
            ui.update_selectize("radar_symbols", choices=all_syms, selected=sorted(list(new_syms)))
        except:
            pass

    @reactive.effect
    @reactive.event(input.radar_interval, ignore_init=True)
    def _update_symbol_choices():
        all_syms = manager.get_universe()
        curr_sel = sorted(list(selected_symbols_radar.get()))
        ui.update_selectize("radar_symbols", choices=all_syms, selected=curr_sel)
        ui.update_selectize("focus_symbol", choices=[""] + curr_sel)

    @reactive.effect
    @reactive.event(input.btn_calc_snapshot)
    def _handle_radar_sync():
        # Strictly gate both symbol population and data syncing behind the button
        try:
            val = input.n_assets_radar()
            n_assets = int(val) if val else 20
        except ValueError:
            n_assets = 20
            
        interval = input.radar_interval()
        
        with ui.Progress(min=0, max=100) as p:
            # 1. Populate Symbols
            p.set(5, message="Refreshing symbols...", detail=f"Fetching top {n_assets} high-volume assets")
            try:
                new_syms = manager.fetcher.get_top_volume_symbols(top_n=n_assets)
            except Exception as e:
                ui.notification_show(f"Market Data Error: {str(e)}", type="error")
                new_syms = []
            syms = sorted(list(set(MANDATORY_CRYPTO).union(new_syms)))
            # Filter ignored
            syms = [s for s in syms if s not in IGNORED_CRYPTO]
            
            selected_symbols_radar.set(set(syms))
            
            # 2. Update UI
            all_syms = manager.get_universe()
            ui.update_selectize("radar_symbols", choices=all_syms, selected=syms)
            ui.update_selectize("focus_symbol", choices=[""] + syms)
            ui.update_selectize("rpg_focus_symbol", choices=[""] + syms)
            
            # 3. Sync data for these symbols (if needed/optional)
            p.set(20, message="Syncing data...", detail="Ensuring cache is up-to-date")
            # In Market Radar, we typically load on-demand during calculation, 
            # but we can do a quick check here if desired.
            
            p.set(100, message="Sync complete")

    @reactive.effect
    def _sync_focus_symbol():
        symbol = input.focus_symbol()
        if symbol:
            selected_symbol_data.set(symbol.upper())

    @reactive.effect
    @reactive.event(input.btn_calc_snapshot)
    async def _():
        logger.log("Market Radar", "INFO", "Snapshot calculation triggered")
        try:
            interval = input.radar_interval()
            logger.log("Market Radar", "INFO", f"Using interval: {interval}")
            
            symbols = list(input.radar_symbols())
            logger.log("Market Radar", "INFO", f"Calculating metrics for {len(symbols)} symbols")
            
            if not symbols:
                ui.notification_show("Please select symbols for analysis.", type="warning")
                return

            with ui.Progress(min=0, max=len(symbols)) as p:
                p.set(message="Analyzing...")
                
                # 1. Prepare Benchmark once
                benchmark_df = manager.load_data(BENCHMARK_SYMBOL, interval)
                benchmark_returns = None
                if benchmark_df is not None and not benchmark_df.empty:
                    b_close = pd.to_numeric(benchmark_df['close'], errors='coerce').ffill().fillna(0)
                    benchmark_returns = b_close.pct_change().dropna()
                
                # Pulse reactive inputs once here
                filter_window = input.filter_window()

                def process_symbol(sym):
                    try:
                        df = manager.load_data(sym, interval)
                        # We need at least window * 30 candles for the breakout score volatility logic
                        df = df.tail(filter_window * 40)
                        if df is not None and not df.empty:
                            return engine.compute_all_metrics(
                                {sym: df}, 
                                interval=interval, 
                                benchmark_symbol=BENCHMARK_SYMBOL,
                                benchmark_returns=benchmark_returns,
                                benchmark_prices=b_close,
                                window=filter_window
                            )
                    except Exception as e:
                        logger.log("Market Radar", "ERROR", f"Error computing {sym}: {e}")
                    return None

                results = []
                # Use a reasonable number of workers
                with ThreadPoolExecutor(max_workers=10) as executor:
                    # Submit all tasks (Excluding nothing during calculation for realtime filtering)
                    future_to_sym = {executor.submit(process_symbol, sym): sym for sym in symbols}
                    
                    # Process as they complete to update progress bar
                    for i, future in enumerate(future_to_sym):
                        sym = future_to_sym[future]
                        try:
                            single_res = future.result()
                            if single_res is not None and not single_res.empty:
                                results.append(single_res.iloc[0])
                        except Exception as e:
                            logger.log("Market Radar", "ERROR", f"Future error for {sym}: {e}")
                        
                        p.set(i + 1, detail=f"Processed {sym}")
                        await reactive.flush()
                
                if not results:
                    ui.notification_show("Failed to compute metrics for any symbols.", type="error")
                    return

                res = pd.DataFrame(results)
                logger.log("Market Radar", "INFO", f"Metrics computation complete. Symbols: {len(res)}")
                
                snapshot_data.set(res)
                ui.notification_show("Market Snapshot updated!", type="success")
                
        except Exception as e:
            logger.log("Market Radar", "ERROR", f"Snapshot error: {str(e)}")
            ui.notification_show(f"Calculation error: {str(e)}", type="error")

    @render.text
    def snapshot_ready():
        return "true" if not snapshot_data.get().empty else "false"

    @render.text
    def rpg_ready():
        return "true" if not rpg_data.get().empty else "false"
    
    @reactive.calc
    def filtered_snapshot_df():
        df = snapshot_data.get()
        if df.empty:
            return df
        
        # Apply Exclude Symbols filter reactively
        # Now we use radar_symbols as positive inclusion
        selected = list(input.radar_symbols())
        if selected:
            df = df[df['symbol'].isin(selected)]
            
        if input.drop_zeros():
            x_col = input.x_axis()
            y_col = input.y_axis()
            z_col = input.z_axis()
            
            # Check X axis
            if x_col in df.columns:
                df = df[df[x_col].abs() > 1e-9]
            
            # Check Y axis
            if y_col in df.columns:
                df = df[df[y_col].abs() > 1e-9]
                
            # Check Z axis if it's not None
            if z_col != "None" and z_col in df.columns:
                df = df[df[z_col].abs() > 1e-9]
            
        return df

    @reactive.calc
    def snapshot_regression_params():
        plot_df = filtered_snapshot_df()
        if len(plot_df) <= 1:
            return None
            
        x, y = input.x_axis(), input.y_axis()
        
        try:
            # Ensure selected columns are numeric
            reg_x = pd.to_numeric(plot_df[x], errors='coerce').values
            reg_y = pd.to_numeric(plot_df[y], errors='coerce').values
            
            # Filter out NaNs or Infs
            mask = np.isfinite(reg_x) & np.isfinite(reg_y)
            reg_x, reg_y = reg_x[mask], reg_y[mask]
            
            if len(reg_x) > 1 and np.std(reg_x) > 1e-12:
                slope, intercept, r_value, p_value, std_err = stats.linregress(reg_x, reg_y)
                
                # Generate line points
                x_range = np.linspace(reg_x.min(), reg_x.max(), 100)
                y_range = intercept + slope * x_range
                
                return {
                    "x_range": x_range,
                    "y_range": y_range,
                    "r_squared": r_value**2,
                    "intercept": intercept,
                    "slope": slope
                }
        except Exception as e:
            logger.log("Market Radar", "ERROR", f"Regression calculation error: {e}")
            
        return None

    @render.data_frame
    def snapshot_table():
        df = filtered_snapshot_df()
        if df.empty:
            return df
        # Only show symbol + columns defined in ALL_METRICS
        cols = ['symbol'] + [c for c in ALL_METRICS if c in df.columns]
        return df[cols]

    @render_widget
    def snapshot_chart():
        plot_df = filtered_snapshot_df()
        if plot_df.empty:
            # Return empty figure with message if possible, or just empty
            fig = go.Figure()
            fig.add_annotation(text="No data matching filters or symbols not loaded", showarrow=False, font=dict(size=20))
            fig.update_layout(
                template="plotly_dark",
                margin=dict(l=80, r=80, t=80, b=100),
                xaxis_title=dict(
                    text=METRIC_LABELS.get(x, x),
                    standoff=30
                ),
                yaxis_title=dict(
                    text=METRIC_LABELS.get(y, y),
                    standoff=30
                ),
                coloraxis_colorbar=dict(
                    title=METRIC_LABELS.get(z, z) if z != "None" else None,
                    x=1.1,
                    len=0.8
                )
            )
            return fig

        x, y, z = input.x_axis(), input.y_axis(), input.z_axis()
        
        # Ensure selected columns are numeric and handle NaNs for Plotly
        for col in [x, y]:
            if col in plot_df.columns:
                plot_df[col] = pd.to_numeric(plot_df[col], errors='coerce').fillna(0)
        
        if z != "None" and z in plot_df.columns:
            plot_df[z] = pd.to_numeric(plot_df[z], errors='coerce').fillna(0)
            # px.scatter size must be positive
            z_min = plot_df[z].min()
            z_max = plot_df[z].max()
            denom = z_max - z_min
            if abs(denom) > 1e-12:
                z_norm = (plot_df[z] - z_min) / denom
            else:
                z_norm = np.zeros(len(plot_df))
            plot_df['z_marker_size'] = z_norm + 1
            
            fig = px.scatter(
                plot_df, x=x, y=y, size='z_marker_size', color=z,
                hover_name='symbol', log_x=input.x_log(), log_y=input.y_log(),
                color_continuous_scale='Spectral_r',
                template="plotly_dark",
                custom_data=['symbol']  # Add symbol to custom data for click events
            )
        else:
            fig = px.scatter(
                plot_df, x=x, y=y, hover_name='symbol',
                log_x=input.x_log(), log_y=input.y_log(),
                template="plotly_dark",
                custom_data=['symbol']  # Add symbol to custom data for click events
            )
            fig.update_traces(marker=dict(color='#00F5FF'))
            
        fig.update_layout(
            margin=dict(l=80, r=80, t=80, b=120),
            showlegend=True,
            legend=dict(
                orientation="h",
                yanchor="top",
                y=-0.2,
                xanchor="center",
                x=0.5
            ),
            xaxis_title=dict(
                text=METRIC_LABELS.get(x, x),
                standoff=40
            ),
            yaxis_title=dict(
                text=METRIC_LABELS.get(y, y),
                standoff=40
            ),
            paper_bgcolor="#0a0a0a",
            plot_bgcolor="#0a0a0a",
            height=600,
            # width=1470,
            font=dict(family="Space Mono", color="white"),
            clickmode='event+select'  # Enable click events
        )

        fig.update_xaxes(gridcolor="#333333", zerolinecolor="#444444", linecolor="white", tickcolor="white")
        fig.update_yaxes(gridcolor="#333333", zerolinecolor="#444444", linecolor="white", tickcolor="white")
                               
        focus_sym = (input.focus_symbol() or "").strip().upper()
        selected_points = None
        unselected_opacity = 0.2
        selection_size = 10

        if focus_sym and focus_sym in plot_df['symbol'].str.upper().values:
            pos_idx = list(plot_df['symbol'].str.upper()).index(focus_sym)
            selected_points = [pos_idx]
            
        if z != "None" and 'z_marker_size' in plot_df.columns:
            size_max = 20
            min_visible = 8

            mask = plot_df['symbol'].astype(str).str.strip().str.upper() == focus_sym

            if mask.any():
                max_val = plot_df['z_marker_size'].max()
                current_val = plot_df.loc[mask, 'z_marker_size'].iloc[0]

                if max_val > 0:
                    sizeref = 2 * max_val / (size_max ** 2)
                    pixel_size = np.sqrt(current_val / sizeref)

                    selection_size = pixel_size if pixel_size >= min_visible else min_visible

        fig.update_traces(
            hovertemplate='<b>%{hovertext}</b><br>' +
                        f'{METRIC_LABELS.get(x, x)}: %{{x}}<br>' +
                        f'{METRIC_LABELS.get(y, y)}: %{{y}}<br>' +
                        '<extra></extra>',
            selectedpoints=selected_points,
            marker=dict(
                line=dict(
                    color="white",
                    width=1
                )
            ),
            selected=dict(
                marker=dict(
                    # color='#FF3B3B',
                    # size=selection_size,
                    opacity=1
                )
            ),
            unselected=dict(
                marker=dict(
                    opacity=unselected_opacity
                )
            )
        )

        # fig.update_xaxes(gridcolor="rgba(255, 255, 255, 0.3)", zerolinecolor="rgba(255, 255, 255, 0.5)", linecolor="white", tickcolor="white")
        # fig.update_yaxes(gridcolor="rgba(255, 255, 255, 0.3)", zerolinecolor="rgba(255, 255, 255, 0.5)", linecolor="white", tickcolor="white")
 
        # --- Regression Line ---
        reg = snapshot_regression_params()
        if input.show_regression(): 
            if reg:
                fig.add_trace(go.Scatter(
                    x=reg["x_range"],
                    y=reg["y_range"],
                    mode='lines',
                    name=f'Fit (R²={reg["r_squared"]:.3f} | intercept={reg["intercept"]:.3f} | slope={reg["slope"]:.3f})',
                    line=dict(color='orange', width=2, dash='dash'),
                    hoverinfo='skip'
                ))

        return fig
    
    @reactive.effect
    @reactive.event(input.snapshot_chart_click)
    def _handle_chart_click():
        """Handle click events on the snapshot chart"""
        click_data = input.snapshot_chart_click()
        
        if click_data is None:
            return
        
        logger.log("Market Radar", "INFO", f"Chart click event: {click_data}")
        
        # Extract the clicked point data
        try:
            # Plotly click data structure: {'points': [{'customdata': [...], ...}]}
            if 'points' in click_data and len(click_data['points']) > 0:
                point = click_data['points'][0]
                
                # Get symbol from customdata or hovertext
                if 'customdata' in point and point['customdata']:
                    symbol = point['customdata'][0]
                elif 'hovertext' in point:
                    symbol = point['hovertext']
                else:
                    logger.log("Market Radar", "WARNING", "No symbol found in click data")
                    return
                
                logger.log("Market Radar", "INFO", f"Selected symbol: {symbol}")
                selected_symbol_data.set(symbol)
                
                # Update Focus Symbol input box
                ui.update_selectize("focus_symbol", selected=symbol)
        except Exception as e:
            logger.log("Market Radar", "ERROR", f"Error handling chart click: {e}")

    @render.ui
    def selected_symbol_info():
        """Display information about the selected symbol from chart click"""
        selected = selected_symbol_data.get()
        
        if selected is None:
            return ui.div(
                ui.p("Click on a point in the chart above to see detailed metrics", 
                     class_="text-muted text-center",
                     style="padding: 20px;")
            )
        
        # Get the full row data for the selected symbol
        df = snapshot_data.get()
        if df.empty:
            return ui.div(ui.p("No data available", class_="text-muted"))
        
        symbol_row = df[df['symbol'] == selected]
        if symbol_row.empty:
            return ui.div(ui.p(f"Symbol {selected} not found", class_="text-muted"))
        
        row = symbol_row.iloc[0]
        
        # TradingView interval mapping
        tv_intervals = {
            '1m': '1', '3m': '3', '5m': '5', '15m': '15', '30m': '30',
            '1h': '60', '2h': '120', '4h': '240', '6h': '360', '8h': '480', '12h': '720',
            '1d': 'D', '3d': '3D', '1w': 'W'
        }
        tv_int = tv_intervals.get(input.radar_interval(), '60')

        # Create a formatted display of all metrics
        metrics_html = f"""
        <div style="padding: 15px;">
            <h4 style="color: #FFD700; margin-bottom: 15px;">
                {selected}
                <a href="{TRADINGVIEW_URL}?symbol=BINANCE:{selected}&interval={tv_int}" target="_blank" 
                   style="font-size: 0.8em; margin-left: 10px; color: #1f77b4; text-decoration: none;">
                    📈 View on TradingView
                </a>
            </h4>
            <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 10px;">
        """
        
        # Add all metrics
        for col in df.columns:
            if col != 'symbol':
                value = row[col]
                label = METRIC_LABELS.get(col, col)
                
                # Format the value
                if isinstance(value, (int, float)):
                    if abs(value) < 0.01:
                        formatted_value = f"{value:.6f}"
                    elif abs(value) < 1:
                        formatted_value = f"{value:.4f}"
                    else:
                        formatted_value = f"{value:.2f}"
                    
                    # Color code based on value
                    if value > 0:
                        color = "#4ade80"  # green
                    elif value < 0:
                        color = "#f87171"  # red
                    else:
                        color = "#94a3b8"  # gray
                else:
                    formatted_value = str(value)
                    color = "#94a3b8"
                
                metrics_html += f"""
                <div style="background: rgba(255,255,255,0.05); padding: 10px; border-radius: 5px;">
                    <div style="font-size: 0.85em; color: #94a3b8;">{label}</div>
                    <div style="font-size: 1.1em; font-weight: bold; color: {color}; font-family: 'Space Mono', monospace;">
                        {formatted_value}
                    </div>
                </div>
                """
        
        metrics_html += """
            </div>
        </div>
        """
        
        return ui.HTML(metrics_html)

    @reactive.Effect
    def _populate_initial_symbols():
        # Use centralized universe instead of local inventory
        all_syms = manager.get_universe()
        n = int(input.n_assets_radar() or 20)
        try:
            syms = manager.fetcher.get_top_volume_symbols(top_n=n)
        except Exception as e:
            logger.log("Market Radar", "ERROR", f"Initial pop-up sync failed: {e}")
            syms = []
            
        new_syms = set(MANDATORY_CRYPTO).union(syms)
        new_syms = {s for s in new_syms if s not in IGNORED_CRYPTO}
        ui.update_selectize("radar_symbols", choices=all_syms, selected=sorted(list(new_syms)), server=True)
        ui.update_selectize("rpg_symbols", choices=all_syms, selected=sorted(list(new_syms)), server=True)

