"""
Interactive charting with Plotly
"""

import plotly.graph_objects as go
from plotly.subplots import make_subplots
import pandas as pd
import numpy as np


def create_candlestick_chart(df, title="Bitcoin Price Chart", show_volume=True):
    """
    Create interactive candlestick chart with Plotly.

    Args:
        df: DataFrame with OHLCV data and timestamp
        title: Chart title
        show_volume: Whether to show volume subplot

    Returns:
        Plotly figure
    """
    # Create figure with secondary y-axis for volume
    if show_volume:
        fig = make_subplots(
            rows=2, cols=1,
            shared_xaxes=True,
            vertical_spacing=0.03,
            row_heights=[0.7, 0.3],
            subplot_titles=(title, "Volume")
        )
    else:
        fig = go.Figure()

    # Convert timestamp to datetime if needed
    if 'timestamp' in df.columns:
        dates = pd.to_datetime(df['timestamp'], unit='ms')
    else:
        dates = df.index

    # Add candlestick trace
    candlestick = go.Candlestick(
        x=dates,
        open=df['open'],
        high=df['high'],
        low=df['low'],
        close=df['close'],
        name='OHLC',
        increasing_line_color='#26a69a',
        decreasing_line_color='#ef5350'
    )

    if show_volume:
        fig.add_trace(candlestick, row=1, col=1)

        # Add volume bars
        colors = ['#26a69a' if close >= open_ else '#ef5350'
                  for close, open_ in zip(df['close'], df['open'])]

        volume = go.Bar(
            x=dates,
            y=df['volume'],
            name='Volume',
            marker_color=colors,
            showlegend=False
        )
        fig.add_trace(volume, row=2, col=1)
    else:
        fig.add_trace(candlestick)

    # Update layout
    fig.update_layout(
        title=title,
        yaxis_title='Price (USD)',
        xaxis_rangeslider_visible=False,
        template='plotly_dark',
        height=800,
        hovermode='x unified'
    )

    if show_volume:
        fig.update_yaxes(title_text="Price (USD)", row=1, col=1)
        fig.update_yaxes(title_text="Volume (BTC)", row=2, col=1)

    return fig


def add_ema_slope_indicator(fig, df, row=1):
    """
    Add EMA Slope indicator to existing chart.

    Args:
        fig: Plotly figure
        df: DataFrame with EMA slope data (must have 'slope', 'ma' columns)
        row: Which row to add the indicator to

    Returns:
        Updated figure
    """
    if 'timestamp' in df.columns:
        dates = pd.to_datetime(df['timestamp'], unit='ms')
    else:
        dates = df.index

    # Add EMA line
    if 'ma' in df.columns:
        fig.add_trace(
            go.Scatter(
                x=dates,
                y=df['ma'],
                name='EMA',
                line=dict(color='yellow', width=1),
                opacity=0.7
            ),
            row=row, col=1
        )

    return fig


def create_ema_slope_chart(df, ntz_threshold=10, title="EMA Slope Indicator"):
    """
    Create EMA Slope indicator chart.

    Args:
        df: DataFrame with slope, acceleration data
        ntz_threshold: No Trade Zone threshold
        title: Chart title

    Returns:
        Plotly figure
    """
    if 'timestamp' in df.columns:
        dates = pd.to_datetime(df['timestamp'], unit='ms')
    else:
        dates = df.index

    fig = go.Figure()

    # Add slope line with color based on value
    slope_colors = []
    for slope in df['slope']:
        if pd.isna(slope):
            slope_colors.append('gray')
        elif slope > ntz_threshold:
            slope_colors.append('#26a69a')  # Bullish - green
        elif slope < -ntz_threshold:
            slope_colors.append('#ef5350')  # Bearish - red
        else:
            slope_colors.append('#baa79b')  # NTZ - gray

    # Plot slope
    fig.add_trace(go.Scatter(
        x=dates,
        y=df['slope'],
        name='Slope',
        line=dict(color='white', width=2),
        fill='tozeroy',
        fillcolor='rgba(255,255,255,0.1)'
    ))

    # Add NTZ threshold lines
    fig.add_hline(
        y=ntz_threshold,
        line_dash="dash",
        line_color="#4bdb62",
        annotation_text="NTZ Upper",
        annotation_position="right"
    )
    fig.add_hline(
        y=-ntz_threshold,
        line_dash="dash",
        line_color="#f42222",
        annotation_text="NTZ Lower",
        annotation_position="right"
    )
    fig.add_hline(
        y=0,
        line_dash="solid",
        line_color="white",
        opacity=0.5
    )

    # Add acceleration if available
    if 'acceleration' in df.columns:
        fig.add_trace(go.Scatter(
            x=dates,
            y=df['acceleration'],
            name='Acceleration',
            mode='markers',
            marker=dict(
                size=4,
                color=df['acceleration'],
                colorscale='Viridis',
                showscale=True,
                colorbar=dict(title="Accel")
            ),
            yaxis='y2'
        ))

    # Update layout
    fig.update_layout(
        title=title,
        yaxis_title='Slope',
        xaxis_title='Time',
        template='plotly_dark',
        height=400,
        hovermode='x unified',
        yaxis2=dict(
            title='Acceleration',
            overlaying='y',
            side='right'
        )
    )

    # Add shaded NTZ region
    fig.add_hrect(
        y0=-ntz_threshold,
        y1=ntz_threshold,
        fillcolor="gray",
        opacity=0.1,
        layer="below",
        line_width=0
    )

    return fig


def create_combined_chart(df, ntz_threshold=10, title="Bitcoin with EMA Slope"):
    """
    Create combined chart with price and EMA slope indicator.

    Args:
        df: DataFrame with OHLCV and EMA slope data
        ntz_threshold: No Trade Zone threshold
        title: Chart title

    Returns:
        Plotly figure with 3 subplots
    """
    # Create subplots: candlestick, volume, slope
    fig = make_subplots(
        rows=3, cols=1,
        shared_xaxes=True,
        vertical_spacing=0.02,
        row_heights=[0.5, 0.2, 0.3],
        subplot_titles=(title, "Volume", "EMA Slope"),
        specs=[[{"secondary_y": False}],
               [{"secondary_y": False}],
               [{"secondary_y": False}]]
    )

    # Properly convert timestamps to datetime
    if 'timestamp' in df.columns:
        # Ensure timestamp is treated as milliseconds
        if pd.api.types.is_integer_dtype(df['timestamp']):
            dates = pd.to_datetime(df['timestamp'], unit='ms')
        elif pd.api.types.is_datetime64_any_dtype(df['timestamp']):
            dates = pd.to_datetime(df['timestamp'])
        else:
            dates = pd.to_datetime(df['timestamp'])
    else:
        if pd.api.types.is_datetime64_any_dtype(df.index):
            dates = df.index
        else:
            dates = pd.to_datetime(df.index, unit='ms')

    # 1. Candlestick chart
    fig.add_trace(
        go.Candlestick(
            x=dates,
            open=df['open'],
            high=df['high'],
            low=df['low'],
            close=df['close'],
            name='Price',
            increasing_line_color='#26a69a',
            decreasing_line_color='#ef5350'
        ),
        row=1, col=1
    )

    # Add EMA line
    if 'ma' in df.columns:
        fig.add_trace(
            go.Scatter(
                x=dates,
                y=df['ma'],
                name=f'EMA',
                line=dict(color='yellow', width=1.5),
                opacity=0.8
            ),
            row=1, col=1
        )

    # Process trading signals and calculate PnL
    if 'signal' in df.columns:
        # Separate entry and exit signals
        buy_mask = df['signal'] == 'BUY'
        sell_mask = df['signal'] == 'SELL'
        exit_long_mask = df['signal'] == 'EXIT_LONG'
        exit_short_mask = df['signal'] == 'EXIT_SHORT'

        # Match trades and calculate PnL
        trades = []
        trade_counter = 0
        current_long = None
        current_short = None

        for idx in df.index:
            signal = df.loc[idx, 'signal']
            timestamp = dates[idx]
            price = df.loc[idx, 'close']
            slope = df.loc[idx, 'slope']

            if signal == 'BUY' and current_long is None:
                current_long = {
                    'entry_idx': idx,
                    'entry_time': timestamp,
                    'entry_price': price,
                    'entry_slope': slope
                }
            elif signal == 'EXIT_LONG' and current_long is not None:
                trade_counter += 1
                pnl_pct = ((price - current_long['entry_price']) / current_long['entry_price']) * 100
                pnl_usd = price - current_long['entry_price']
                trades.append({
                    'trade_num': trade_counter,
                    'type': 'LONG',
                    'entry_idx': current_long['entry_idx'],
                    'exit_idx': idx,
                    'entry_time': current_long['entry_time'],
                    'exit_time': timestamp,
                    'entry_price': current_long['entry_price'],
                    'exit_price': price,
                    'entry_slope': current_long['entry_slope'],
                    'exit_slope': slope,
                    'pnl_pct': pnl_pct,
                    'pnl_usd': pnl_usd
                })
                current_long = None
            elif signal == 'SELL' and current_short is None:
                current_short = {
                    'entry_idx': idx,
                    'entry_time': timestamp,
                    'entry_price': price,
                    'entry_slope': slope
                }
            elif signal == 'EXIT_SHORT' and current_short is not None:
                trade_counter += 1
                pnl_pct = ((current_short['entry_price'] - price) / current_short['entry_price']) * 100
                pnl_usd = current_short['entry_price'] - price
                trades.append({
                    'trade_num': trade_counter,
                    'type': 'SHORT',
                    'entry_idx': current_short['entry_idx'],
                    'exit_idx': idx,
                    'entry_time': current_short['entry_time'],
                    'exit_time': timestamp,
                    'entry_price': current_short['entry_price'],
                    'exit_price': price,
                    'entry_slope': current_short['entry_slope'],
                    'exit_slope': slope,
                    'pnl_pct': pnl_pct,
                    'pnl_usd': pnl_usd
                })
                current_short = None

        # Add entry signals (triangles)
        if buy_mask.any():
            buy_dates_signal = dates[buy_mask]
            buy_prices = df.loc[buy_mask, 'low'] * 0.995
            buy_slopes = df.loc[buy_mask, 'slope']

            hover_text = [
                f"<b>LONG ENTRY</b><br>" +
                f"Time: {dt}<br>" +
                f"Price: ${price:,.2f}<br>" +
                f"Slope: {slope:.2f}"
                for dt, price, slope in zip(buy_dates_signal, df.loc[buy_mask, 'close'], buy_slopes)
            ]

            fig.add_trace(
                go.Scatter(
                    x=buy_dates_signal,
                    y=buy_prices,
                    mode='markers',
                    name='Long Entry',
                    marker=dict(symbol='triangle-up', size=14, color='lime', line=dict(width=1, color='darkgreen')),
                    hovertext=hover_text,
                    hoverinfo='text'
                ),
                row=1, col=1
            )

        if sell_mask.any():
            sell_dates_signal = dates[sell_mask]
            sell_prices = df.loc[sell_mask, 'high'] * 1.005
            sell_slopes = df.loc[sell_mask, 'slope']

            hover_text = [
                f"<b>SHORT ENTRY</b><br>" +
                f"Time: {dt}<br>" +
                f"Price: ${price:,.2f}<br>" +
                f"Slope: {slope:.2f}"
                for dt, price, slope in zip(sell_dates_signal, df.loc[sell_mask, 'close'], sell_slopes)
            ]

            fig.add_trace(
                go.Scatter(
                    x=sell_dates_signal,
                    y=sell_prices,
                    mode='markers',
                    name='Short Entry',
                    marker=dict(symbol='triangle-down', size=14, color='red', line=dict(width=1, color='darkred')),
                    hovertext=hover_text,
                    hoverinfo='text'
                ),
                row=1, col=1
            )

        # Add exit signals (circles) with trade numbers and PnL
        if exit_long_mask.any():
            exit_long_dates = dates[exit_long_mask]
            exit_long_prices = df.loc[exit_long_mask, 'high'] * 1.002

            # Create hover text and annotations with trade numbers
            hover_text = []
            annotations = []

            for idx in df.index[exit_long_mask]:
                # Find matching trade
                matching_trade = next((t for t in trades if t['exit_idx'] == idx and t['type'] == 'LONG'), None)
                if matching_trade:
                    # Simplified hover text - just PnL info
                    pnl_color = 'green' if matching_trade['pnl_pct'] > 0 else 'red'
                    text = (
                        f"<b>Trade #{matching_trade['trade_num']} - LONG</b><br>" +
                        f"PnL: <b style='color:{pnl_color}'>${matching_trade['pnl_usd']:+,.2f} ({matching_trade['pnl_pct']:+.2f}%)</b><br>" +
                        f"Entry: ${matching_trade['entry_price']:,.2f}<br>" +
                        f"Exit: ${matching_trade['exit_price']:,.2f}"
                    )
                    hover_text.append(text)

                    # Add text annotation with trade number
                    annotations.append(dict(
                        x=dates[idx],
                        y=df.loc[idx, 'high'] * 1.008,
                        text=f"#{matching_trade['trade_num']}",
                        showarrow=False,
                        font=dict(size=10, color='black', family='Arial Black'),
                        xref='x',
                        yref='y'
                    ))
                else:
                    text = f"<b>LONG EXIT</b><br>Price: ${df.loc[idx, 'close']:,.2f}"
                    hover_text.append(text)

            fig.add_trace(
                go.Scatter(
                    x=exit_long_dates,
                    y=exit_long_prices,
                    mode='markers',
                    name='Long Exit',
                    marker=dict(symbol='circle', size=12, color='lime', line=dict(width=2, color='darkgreen')),
                    hovertext=hover_text,
                    hoverinfo='text'
                ),
                row=1, col=1
            )

            # Add annotations to the figure
            for ann in annotations:
                fig.add_annotation(ann, row=1, col=1)

        if exit_short_mask.any():
            exit_short_dates = dates[exit_short_mask]
            exit_short_prices = df.loc[exit_short_mask, 'low'] * 0.998

            # Create hover text and annotations with trade numbers
            hover_text = []
            annotations = []

            for idx in df.index[exit_short_mask]:
                # Find matching trade
                matching_trade = next((t for t in trades if t['exit_idx'] == idx and t['type'] == 'SHORT'), None)
                if matching_trade:
                    # Simplified hover text - just PnL info
                    pnl_color = 'green' if matching_trade['pnl_pct'] > 0 else 'red'
                    text = (
                        f"<b>Trade #{matching_trade['trade_num']} - SHORT</b><br>" +
                        f"PnL: <b style='color:{pnl_color}'>${matching_trade['pnl_usd']:+,.2f} ({matching_trade['pnl_pct']:+.2f}%)</b><br>" +
                        f"Entry: ${matching_trade['entry_price']:,.2f}<br>" +
                        f"Exit: ${matching_trade['exit_price']:,.2f}"
                    )
                    hover_text.append(text)

                    # Add text annotation with trade number
                    annotations.append(dict(
                        x=dates[idx],
                        y=df.loc[idx, 'low'] * 0.992,
                        text=f"#{matching_trade['trade_num']}",
                        showarrow=False,
                        font=dict(size=10, color='black', family='Arial Black'),
                        xref='x',
                        yref='y'
                    ))
                else:
                    text = f"<b>SHORT EXIT</b><br>Price: ${df.loc[idx, 'close']:,.2f}"
                    hover_text.append(text)

            fig.add_trace(
                go.Scatter(
                    x=exit_short_dates,
                    y=exit_short_prices,
                    mode='markers',
                    name='Short Exit',
                    marker=dict(symbol='circle', size=12, color='red', line=dict(width=2, color='darkred')),
                    hovertext=hover_text,
                    hoverinfo='text'
                ),
                row=1, col=1
            )

            # Add annotations to the figure
            for ann in annotations:
                fig.add_annotation(ann, row=1, col=1)

    # 2. Volume bars
    colors = ['#26a69a' if close >= open_ else '#ef5350'
              for close, open_ in zip(df['close'], df['open'])]

    fig.add_trace(
        go.Bar(
            x=dates,
            y=df['volume'],
            name='Volume',
            marker_color=colors,
            showlegend=False
        ),
        row=2, col=1
    )

    # 3. EMA Slope - Single continuous line with dynamic coloring (Pine Script style)
    if 'slope' in df.columns:
        # Calculate colors based on Pine Script logic
        # Color changes based on slope position and momentum
        line_colors = []
        fill_colors = []

        for i in range(len(df)):
            slope = df['slope'].iloc[i]
            prev_slope = df['slope'].iloc[i-1] if i > 0 else slope

            if pd.isna(slope):
                line_colors.append('rgba(186, 167, 167, 0.7)')  # NTZ gray
                fill_colors.append('rgba(186, 167, 167, 0.3)')
            elif slope > ntz_threshold:
                # Bullish zone
                if slope > prev_slope:
                    # Accelerating up - bright green
                    line_colors.append('rgba(38, 255, 52, 1)')  # cUPb
                    fill_colors.append('rgba(38, 255, 52, 0.4)')
                else:
                    # Decelerating - green
                    line_colors.append('rgba(38, 255, 72, 1)')  # cUP
                    fill_colors.append('rgba(38, 255, 72, 0.5)')
            elif slope < -ntz_threshold:
                # Bearish zone
                if slope <= prev_slope:
                    # Accelerating down - bright red
                    line_colors.append('rgba(229, 18, 18, 1)')  # cLPb
                    fill_colors.append('rgba(229, 18, 18, 0.4)')
                else:
                    # Decelerating - red
                    line_colors.append('rgba(255, 20, 20, 1)')  # cLP
                    fill_colors.append('rgba(255, 20, 20, 0.4)')
            else:
                # In NTZ - gray/black
                line_colors.append('rgba(186, 167, 167, 0.7)')  # cNTZ
                fill_colors.append('rgba(186, 167, 167, 0.3)')

        # Plot filled area first (background)
        fig.add_trace(
            go.Scatter(
                x=dates,
                y=df['slope'],
                name='Slope Fill',
                fill='tozeroy',
                fillcolor='rgba(186, 167, 167, 0.2)',
                line=dict(width=0),
                showlegend=False,
                hoverinfo='skip'
            ),
            row=3, col=1
        )

        # Plot the main slope line with segment coloring
        # Split into segments for color changes
        segments = []
        current_segment_x = [dates.iloc[0]]
        current_segment_y = [df['slope'].iloc[0]]
        current_color = line_colors[0]

        for i in range(1, len(df)):
            if line_colors[i] != current_color:
                # Color changed - finish current segment
                current_segment_x.append(dates.iloc[i])
                current_segment_y.append(df['slope'].iloc[i])
                segments.append({
                    'x': current_segment_x,
                    'y': current_segment_y,
                    'color': current_color
                })
                # Start new segment
                current_segment_x = [dates.iloc[i]]
                current_segment_y = [df['slope'].iloc[i]]
                current_color = line_colors[i]
            else:
                current_segment_x.append(dates.iloc[i])
                current_segment_y.append(df['slope'].iloc[i])

        # Add final segment
        segments.append({
            'x': current_segment_x,
            'y': current_segment_y,
            'color': current_color
        })

        # Plot each segment - group them as one legend item
        for idx, segment in enumerate(segments):
            fig.add_trace(
                go.Scatter(
                    x=segment['x'],
                    y=segment['y'],
                    name='Slope',
                    legendgroup='slope',  # Group all segments together
                    line=dict(color=segment['color'], width=2.5),
                    mode='lines',
                    showlegend=idx == 0,  # Only show first segment in legend
                    hoverinfo='skip'  # Skip hover on colored segments
                ),
                row=3, col=1
            )

        # Add invisible overlay for hover data (single slope value)
        fig.add_trace(
            go.Scatter(
                x=dates,
                y=df['slope'],
                name='Slope',
                legendgroup='slope',
                line=dict(width=0),  # Invisible
                mode='lines',
                showlegend=False,
                hovertemplate='Slope: %{y:.2f}<extra></extra>',
                opacity=0
            ),
            row=3, col=1
        )

        # Add acceleration circles (from Pine Script)
        # plot(maAcc, 'MA Accel', color = c_Acc, style=plot.style_circles, linewidth=4)
        if 'acceleration' in df.columns:
            # Pine Script logic for acceleration colors
            accel_threshold = 20  # accTh from Pine Script
            accel_colors = []
            accel_sizes = []

            for i in range(len(df)):
                accel = df['acceleration'].iloc[i]
                close_price = df['close'].iloc[i]
                open_price = df['open'].iloc[i]

                # Calculate transparency (trspa from Pine Script)
                # trspa = maAcc < accTh ? 92 : (100 - maAcc *1.5)
                if accel < accel_threshold:
                    opacity = 0.08  # 92% transparent
                else:
                    opacity = min(1.0, (100 - accel * 1.5) / 100)
                    opacity = max(0.08, opacity)  # At least 8% visible

                # Color logic from Pine Script
                # c_Acc = maAcc > 0.3 * maAcc and close > open ? cyan : maAcc > 0.3 * maAcc and close < open ? pink : gray
                if accel > 0.3 and close_price > open_price:
                    # Bullish acceleration - cyan
                    accel_colors.append(f'rgba(10, 246, 255, {opacity})')
                elif accel > 0.3 and close_price < open_price:
                    # Bearish acceleration - pink/magenta
                    accel_colors.append(f'rgba(239, 2, 77, {opacity})')
                else:
                    # Low acceleration - gray
                    accel_colors.append(f'rgba(160, 160, 160, {opacity})')

                # Size based on acceleration magnitude
                accel_sizes.append(min(12, 4 + accel / 10))

            fig.add_trace(
                go.Scatter(
                    x=dates,
                    y=df['acceleration'],
                    name='Acceleration',
                    mode='markers',
                    marker=dict(
                        size=accel_sizes,
                        color=accel_colors,
                        symbol='circle',
                        line=dict(width=0)
                    ),
                    showlegend=True,
                    hovertemplate='Acceleration: %{y:.2f}<extra></extra>',
                    yaxis='y4'  # Secondary y-axis for acceleration
                ),
                row=3, col=1
            )

        # Add NTZ threshold lines as scatter traces (works better with subplots)
        fig.add_trace(
            go.Scatter(
                x=[dates.iloc[0], dates.iloc[-1]],
                y=[ntz_threshold, ntz_threshold],
                name='NTZ Upper',
                line=dict(color='#4bdb62', width=2, dash='dash'),
                showlegend=True,
                hoverinfo='skip'
            ),
            row=3, col=1
        )

        fig.add_trace(
            go.Scatter(
                x=[dates.iloc[0], dates.iloc[-1]],
                y=[-ntz_threshold, -ntz_threshold],
                name='NTZ Lower',
                line=dict(color='#f42222', width=2, dash='dash'),
                showlegend=True,
                hoverinfo='skip'
            ),
            row=3, col=1
        )

        fig.add_trace(
            go.Scatter(
                x=[dates.iloc[0], dates.iloc[-1]],
                y=[0, 0],
                name='Zero Line',
                line=dict(color='white', width=1, dash='solid'),
                opacity=0.3,
                showlegend=False,
                hoverinfo='skip'
            ),
            row=3, col=1
        )

        # Add shaded NTZ region using shapes (works with subplots)
        fig.add_shape(
            type="rect",
            xref="x3",
            yref="y3",
            x0=dates.iloc[0],
            x1=dates.iloc[-1],
            y0=-ntz_threshold,
            y1=ntz_threshold,
            fillcolor="gray",
            opacity=0.15,
            layer="below",
            line_width=0
        )

    # Update layout
    fig.update_layout(
        template='plotly_dark',
        height=1000,
        hovermode='x unified',
        showlegend=True,
        xaxis_rangeslider_visible=False,
        # Ensure proper datetime formatting
        xaxis=dict(
            type='date',
            rangeslider=dict(visible=False)
        ),
        xaxis2=dict(type='date'),
        xaxis3=dict(type='date'),
        # Secondary y-axis for acceleration (overlaying slope)
        yaxis4=dict(
            title='Acceleration',
            overlaying='y3',
            side='right',
            showgrid=False,
            range=[0, 60]  # Acceleration typically 0-50 range
        )
    )

    # Update axes with proper formatting
    fig.update_yaxes(title_text="Price (USD)", row=1, col=1)
    fig.update_yaxes(title_text="Volume (BTC)", row=2, col=1)

    # Slope axis - auto-range based on actual data
    if 'slope' in df.columns:
        slope_min = df['slope'].min()
        slope_max = df['slope'].max()
        # Add 10% padding for visual clarity
        padding = (slope_max - slope_min) * 0.1
        fig.update_yaxes(
            title_text="Slope",
            range=[slope_min - padding, slope_max + padding],
            row=3, col=1
        )
    else:
        fig.update_yaxes(title_text="Slope", row=3, col=1)

    # Ensure all x-axes are synchronized and properly formatted
    fig.update_xaxes(title_text="Time", row=3, col=1, type='date')
    fig.update_xaxes(type='date', row=1, col=1)
    fig.update_xaxes(type='date', row=2, col=1)

    return fig
