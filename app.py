#!/usr/bin/env python3
"""
Interactive Bitcoin Chart Web Application
Real-time timeframe switching and parameter adjustment
"""

import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import sys

from database.connection import db
from database.queries import query_ohlcv_range, get_latest_timestamp, get_earliest_timestamp
from indicators.ema_slope import calculate_ema_slope
from visualization.timeframe import resample_ohlcv, get_timeframe_description
from visualization.chart import create_combined_chart


# Page configuration
st.set_page_config(
    page_title="Bitcoin EMA Slope Analyzer",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for better styling
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        font-weight: bold;
        color: #1f77b4;
        margin-bottom: 0.5rem;
    }
    .sub-header {
        font-size: 1.2rem;
        color: #666;
        margin-bottom: 2rem;
    }
    .metric-container {
        background-color: #f0f2f6;
        padding: 1rem;
        border-radius: 0.5rem;
        margin: 0.5rem 0;
    }
</style>
""", unsafe_allow_html=True)


@st.cache_data(ttl=300)  # Cache for 5 minutes
def load_data(start_ms, end_ms):
    """Load OHLCV data from database"""
    with db.connection() as conn:
        data = query_ohlcv_range(conn, start_ms, end_ms)

    if not data:
        return None

    df = pd.DataFrame(data, columns=[
        'timestamp', 'open', 'high', 'low', 'close', 'volume',
        'quote_volume', 'trades', 'taker_buy_base', 'taker_buy_quote'
    ])

    return df


@st.cache_data
def get_database_range():
    """Get the available data range from database"""
    with db.connection() as conn:
        earliest = get_earliest_timestamp(conn)
        latest = get_latest_timestamp(conn)
    return earliest, latest


def main():
    # Header
    st.markdown('<div class="main-header">📈 Bitcoin EMA Slope Analyzer</div>', unsafe_allow_html=True)
    st.markdown('<div class="sub-header">Interactive multi-timeframe chart with EMA Slope indicator</div>', unsafe_allow_html=True)

    # Get database range
    try:
        earliest_ms, latest_ms = get_database_range()
        earliest_date = datetime.fromtimestamp(earliest_ms / 1000)
        latest_date = datetime.fromtimestamp(latest_ms / 1000)
    except Exception as e:
        st.error(f"Error connecting to database: {e}")
        st.info("Make sure the database exists and is initialized.")
        return

    # Sidebar controls
    st.sidebar.header("⚙️ Chart Settings")

    # Timeframe selector
    timeframe = st.sidebar.selectbox(
        "📊 Timeframe",
        options=['1m', '5m', '10m', '15m', '30m', '1h', '2h', '4h', '1d', '1w'],
        index=5,  # Default to 1h
        help="Select the candle timeframe"
    )

    # Date range selector
    st.sidebar.subheader("📅 Date Range")

    # Quick range presets
    preset = st.sidebar.radio(
        "Quick Range",
        options=['Last 24h', 'Last 3 days', 'Last 7 days', 'Last 30 days', 'Last 90 days', 'Last year', 'All time', 'Custom'],
        index=3  # Default to Last 30 days
    )

    # Calculate date range based on preset
    if preset == 'Custom':
        col1, col2 = st.sidebar.columns(2)
        with col1:
            start_date = st.date_input(
                "Start Date",
                value=(latest_date - timedelta(days=30)).date(),
                min_value=earliest_date.date(),
                max_value=latest_date.date()
            )
        with col2:
            end_date = st.date_input(
                "End Date",
                value=latest_date.date(),
                min_value=earliest_date.date(),
                max_value=latest_date.date()
            )

        start_time = datetime.combine(start_date, datetime.min.time())
        end_time = datetime.combine(end_date, datetime.max.time())
    else:
        preset_days = {
            'Last 24h': 1,
            'Last 3 days': 3,
            'Last 7 days': 7,
            'Last 30 days': 30,
            'Last 90 days': 90,
            'Last year': 365,
            'All time': None
        }

        days = preset_days[preset]
        if days is None:
            start_time = earliest_date
            end_time = latest_date
        else:
            end_time = latest_date
            start_time = latest_date - timedelta(days=days)

    # EMA Slope parameters
    st.sidebar.subheader("🎯 Indicator Parameters")

    smooth_bars = st.sidebar.slider(
        "Smooth Bars",
        min_value=1,
        max_value=10,
        value=3,
        help="Number of bars for slope calculation"
    )

    ma_length = st.sidebar.slider(
        "EMA Length",
        min_value=5,
        max_value=200,
        value=9,
        help="Moving average period"
    )

    ntz_threshold = st.sidebar.slider(
        "NTZ Threshold",
        min_value=5,
        max_value=50,
        value=10,
        help="No Trade Zone threshold (±)"
    )

    ma_type = st.sidebar.selectbox(
        "MA Type",
        options=['EMA', 'SMA', 'DEMA', 'TEMA', 'WMA', 'HMA'],
        index=0,
        help="Type of moving average"
    )

    # Display info
    st.sidebar.markdown("---")
    st.sidebar.info(
        f"**Database Info**\n\n"
        f"📅 Earliest: {earliest_date.strftime('%Y-%m-%d')}\n\n"
        f"📅 Latest: {latest_date.strftime('%Y-%m-%d')}\n\n"
        f"📊 Total days: {(latest_date - earliest_date).days}"
    )

    # Load button
    load_chart = st.sidebar.button("🔄 Load Chart", type="primary", use_container_width=True)

    # Main content area
    if load_chart or 'chart_loaded' not in st.session_state:
        st.session_state.chart_loaded = True

        # Convert to milliseconds
        start_ms = int(start_time.timestamp() * 1000)
        end_ms = int(end_time.timestamp() * 1000)

        # Display loading info
        with st.spinner(f'Loading {get_timeframe_description(timeframe)} data...'):
            # Load data
            df = load_data(start_ms, end_ms)

            if df is None or len(df) == 0:
                st.error("No data found for the selected period!")
                return

            # Display data info
            col1, col2, col3, col4 = st.columns(4)

            with col1:
                st.metric("1-minute Candles", f"{len(df):,}")

            # Resample if needed
            if timeframe != '1m':
                with st.spinner(f'Resampling to {get_timeframe_description(timeframe)}...'):
                    df = resample_ohlcv(df, timeframe)

            with col2:
                st.metric(f"{get_timeframe_description(timeframe)} Candles", f"{len(df):,}")

            # Calculate indicator
            with st.spinner('Calculating EMA Slope indicator...'):
                lookback = min(500, len(df) // 2)
                df = calculate_ema_slope(
                    df,
                    smooth_bars=smooth_bars,
                    ma_length=ma_length,
                    ntz_threshold=ntz_threshold,
                    ma_type=ma_type,
                    lookback=lookback
                )

                df = df.dropna(subset=['close', 'open', 'high', 'low'])

            with col3:
                st.metric("Valid Candles", f"{len(df):,}")

            # Count signals
            if 'signal' in df.columns:
                signal_counts = df['signal'].value_counts()
                buy_signals = signal_counts.get('BUY', 0)
                sell_signals = signal_counts.get('SELL', 0)
                with col4:
                    st.metric("Signals", f"🟢 {buy_signals} | 🔴 {sell_signals}")

        # Create and display chart
        with st.spinner('Generating chart...'):
            title = f"Bitcoin {get_timeframe_description(timeframe)} | {ma_type}({ma_length}) | NTZ: ±{ntz_threshold}"

            fig = create_combined_chart(
                df,
                ntz_threshold=ntz_threshold,
                title=title
            )

            # Make chart responsive
            fig.update_layout(
                autosize=True,
                margin=dict(l=50, r=50, t=80, b=50),
            )

            st.plotly_chart(fig, use_container_width=True, height=1000)

        # Display statistics
        st.subheader("📊 Statistics")

        col1, col2, col3, col4 = st.columns(4)

        latest_price = df['close'].iloc[-1]
        earliest_price = df['close'].iloc[0]
        price_change = latest_price - earliest_price
        price_change_pct = (price_change / earliest_price) * 100

        with col1:
            st.metric(
                "Current Price",
                f"${latest_price:,.2f}",
                f"{price_change_pct:+.2f}%"
            )

        with col2:
            st.metric(
                "Period High",
                f"${df['high'].max():,.2f}"
            )

        with col3:
            st.metric(
                "Period Low",
                f"${df['low'].min():,.2f}"
            )

        with col4:
            st.metric(
                "Total Volume",
                f"{df['volume'].sum():,.2f} BTC"
            )

        # Trade Performance Analysis
        if 'signal' in df.columns:
            st.subheader("💰 Trade Performance")

            # Calculate trades
            trades = []
            current_long = None
            current_short = None

            for idx in df.index:
                signal = df.loc[idx, 'signal']
                timestamp = df.loc[idx, 'timestamp']
                price = df.loc[idx, 'close']
                slope = df.loc[idx, 'slope']

                if signal == 'BUY' and current_long is None:
                    current_long = {'entry_idx': idx, 'entry_price': price}
                elif signal == 'EXIT_LONG' and current_long is not None:
                    pnl_pct = ((price - current_long['entry_price']) / current_long['entry_price']) * 100
                    trades.append({'type': 'LONG', 'pnl_pct': pnl_pct, 'pnl_usd': price - current_long['entry_price']})
                    current_long = None
                elif signal == 'SELL' and current_short is None:
                    current_short = {'entry_idx': idx, 'entry_price': price}
                elif signal == 'EXIT_SHORT' and current_short is not None:
                    pnl_pct = ((current_short['entry_price'] - price) / current_short['entry_price']) * 100
                    trades.append({'type': 'SHORT', 'pnl_pct': pnl_pct, 'pnl_usd': current_short['entry_price'] - price})
                    current_short = None

            if trades:
                total_trades = len(trades)
                winning_trades = sum(1 for t in trades if t['pnl_pct'] > 0)
                losing_trades = sum(1 for t in trades if t['pnl_pct'] < 0)
                win_rate = (winning_trades / total_trades * 100) if total_trades > 0 else 0
                total_pnl = sum(t['pnl_usd'] for t in trades)
                avg_pnl = total_pnl / total_trades if total_trades > 0 else 0
                avg_win = sum(t['pnl_usd'] for t in trades if t['pnl_pct'] > 0) / winning_trades if winning_trades > 0 else 0
                avg_loss = sum(t['pnl_usd'] for t in trades if t['pnl_pct'] < 0) / losing_trades if losing_trades > 0 else 0

                col1, col2, col3, col4, col5 = st.columns(5)

                with col1:
                    st.metric("Total Trades", f"{total_trades}")

                with col2:
                    st.metric("Win Rate", f"{win_rate:.1f}%", f"{winning_trades}W / {losing_trades}L")

                with col3:
                    pnl_color = "normal" if total_pnl >= 0 else "inverse"
                    st.metric("Total PnL", f"${total_pnl:,.2f}", delta_color=pnl_color)

                with col4:
                    st.metric("Avg Win", f"${avg_win:,.2f}")

                with col5:
                    st.metric("Avg Loss", f"${avg_loss:,.2f}")

                # Show trade breakdown
                st.markdown("**Trade Breakdown:**")
                long_trades = [t for t in trades if t['type'] == 'LONG']
                short_trades = [t for t in trades if t['type'] == 'SHORT']

                col1, col2 = st.columns(2)
                with col1:
                    if long_trades:
                        long_pnl = sum(t['pnl_usd'] for t in long_trades)
                        long_wins = sum(1 for t in long_trades if t['pnl_pct'] > 0)
                        st.write(f"🟢 **Longs:** {len(long_trades)} trades, {long_wins} wins, ${long_pnl:,.2f} PnL")

                with col2:
                    if short_trades:
                        short_pnl = sum(t['pnl_usd'] for t in short_trades)
                        short_wins = sum(1 for t in short_trades if t['pnl_pct'] > 0)
                        st.write(f"🔴 **Shorts:** {len(short_trades)} trades, {short_wins} wins, ${short_pnl:,.2f} PnL")

            else:
                st.info("No completed trades in this period. Adjust date range or parameters to see more signals.")

        # Signal distribution
        if 'signal' in df.columns:
            st.subheader("📍 Signal Distribution")

            signal_df = df[df['signal'] != 'HOLD']['signal'].value_counts().reset_index()
            signal_df.columns = ['Signal', 'Count']

            col1, col2 = st.columns([1, 2])

            with col1:
                st.dataframe(signal_df, hide_index=True, use_container_width=True)

            with col2:
                # Show recent signals
                st.write("**Recent Signals (Last 10)**")
                recent_signals = df[df['signal'] != 'HOLD'].tail(10)[['timestamp', 'signal', 'close', 'slope']].copy()
                recent_signals['timestamp'] = pd.to_datetime(recent_signals['timestamp'], unit='ms')
                recent_signals['close'] = recent_signals['close'].apply(lambda x: f"${x:,.2f}")
                recent_signals['slope'] = recent_signals['slope'].apply(lambda x: f"{x:.2f}")
                st.dataframe(recent_signals, hide_index=True, use_container_width=True)

        # Current indicator values
        st.subheader("🎯 Current Indicator Values")

        col1, col2, col3 = st.columns(3)

        current_slope = df['slope'].iloc[-1]
        current_signal = df['signal'].iloc[-1]
        current_in_ntz = df['in_ntz'].iloc[-1]

        with col1:
            slope_color = "🟢" if current_slope > ntz_threshold else "🔴" if current_slope < -ntz_threshold else "⚪"
            st.metric(
                "Current Slope",
                f"{slope_color} {current_slope:.2f}",
                f"{'Bullish' if current_slope > ntz_threshold else 'Bearish' if current_slope < -ntz_threshold else 'Neutral'}"
            )

        with col2:
            st.metric(
                "Current Signal",
                current_signal,
                "Active" if current_signal != 'HOLD' else "Waiting"
            )

        with col3:
            st.metric(
                "Market State",
                "No Trade Zone" if current_in_ntz else "Trending",
                "🚫 Avoid" if current_in_ntz else "✅ Trade"
            )

    else:
        st.info("👈 Configure your chart settings in the sidebar and click 'Load Chart'")

        # Show quick help
        st.markdown("""
        ### 🚀 Quick Start

        1. **Select Timeframe** - Choose from 1m to 1w candles
        2. **Pick Date Range** - Use presets or custom dates
        3. **Adjust Parameters** - Fine-tune the EMA Slope indicator
        4. **Load Chart** - Click the button to generate your chart

        ### 📊 Chart Features

        - **Interactive Zoom** - Click and drag to zoom into any region
        - **Pan** - Click and drag to move around
        - **Reset** - Double-click to reset the view
        - **Toggle Traces** - Click legend items to show/hide
        - **Hover Data** - Hover over candles for detailed info

        ### 🎯 Trading Signals

        - **🟢 BUY**: Slope crosses above +{ntz_threshold} (bullish momentum)
        - **🔴 SELL**: Slope crosses below -{ntz_threshold} (bearish momentum)
        - **EXIT_LONG**: Slope enters NTZ from above (take profits)
        - **EXIT_SHORT**: Slope enters NTZ from below (cover shorts)
        - **HOLD**: Slope within ±{ntz_threshold} (no trade zone)
        """)


if __name__ == "__main__":
    main()
