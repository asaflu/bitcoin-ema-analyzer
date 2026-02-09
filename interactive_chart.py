#!/usr/bin/env python3
"""
Interactive Bitcoin Chart with EMA Slope Indicator
Supports multiple timeframes with dynamic resampling
"""

import sys
import argparse
from datetime import datetime, timedelta
import pandas as pd

from database.connection import db
from database.queries import query_ohlcv_range, get_latest_timestamp
from indicators.ema_slope import calculate_ema_slope
from visualization.timeframe import resample_ohlcv, get_timeframe_description
from visualization.chart import create_combined_chart


def main():
    parser = argparse.ArgumentParser(
        description='Interactive Bitcoin chart with EMA Slope indicator'
    )

    parser.add_argument(
        '--timeframe', '-t',
        type=str,
        default='1h',
        choices=['1m', '5m', '10m', '15m', '30m', '1h', '2h', '4h', '1d', '1w'],
        help='Timeframe for the chart (default: 1h)'
    )

    parser.add_argument(
        '--days', '-d',
        type=int,
        default=7,
        help='Number of days of historical data to display (default: 7)'
    )

    parser.add_argument(
        '--smooth-bars',
        type=int,
        default=3,
        help='EMA Slope smooth bars parameter (default: 3)'
    )

    parser.add_argument(
        '--ma-length',
        type=int,
        default=9,
        help='EMA length parameter (default: 9)'
    )

    parser.add_argument(
        '--ntz-threshold',
        type=int,
        default=10,
        help='No Trade Zone threshold (default: 10)'
    )

    parser.add_argument(
        '--output', '-o',
        type=str,
        default=None,
        help='Save chart to HTML file instead of displaying'
    )

    args = parser.parse_args()

    print("=" * 70)
    print("INTERACTIVE BITCOIN CHART WITH EMA SLOPE")
    print("=" * 70)
    print(f"Timeframe: {get_timeframe_description(args.timeframe)}")
    print(f"Historical period: {args.days} days")
    print(f"EMA Slope parameters: smoothBars={args.smooth_bars}, "
          f"maLength={args.ma_length}, NTZ={args.ntz_threshold}")
    print()

    # Get data from database
    print("Loading data from database...")
    with db.connection() as conn:
        latest = get_latest_timestamp(conn)

        # Calculate start time
        start_time = latest - (args.days * 24 * 60 * 60 * 1000)

        print(f"Period: {datetime.fromtimestamp(start_time/1000)} to "
              f"{datetime.fromtimestamp(latest/1000)}")
        print("Fetching 1-minute data...")

        data = query_ohlcv_range(conn, start_time, latest)

    if not data:
        print("ERROR: No data found")
        return 1

    # Convert to DataFrame
    df = pd.DataFrame(data, columns=[
        'timestamp', 'open', 'high', 'low', 'close', 'volume',
        'quote_volume', 'trades', 'taker_buy_base', 'taker_buy_quote'
    ])

    print(f"Loaded {len(df):,} 1-minute candles")

    # Resample to target timeframe if not 1m
    if args.timeframe != '1m':
        print(f"Resampling to {get_timeframe_description(args.timeframe)}...")
        df = resample_ohlcv(df, args.timeframe)
        print(f"Resampled to {len(df):,} candles")

    print()

    # Calculate EMA Slope indicator
    print("Calculating EMA Slope indicator...")
    # Use adaptive lookback based on data length
    lookback = min(500, len(df) // 2)
    df = calculate_ema_slope(
        df,
        smooth_bars=args.smooth_bars,
        ma_length=args.ma_length,
        ntz_threshold=args.ntz_threshold,
        ma_type='EMA',
        lookback=lookback
    )

    # Drop NaN values
    df = df.dropna()
    print(f"Valid candles after indicator calculation: {len(df):,}")
    print()

    # Show signal distribution
    if 'signal' in df.columns:
        signal_counts = df['signal'].value_counts()
        print("Signal distribution:")
        for signal, count in signal_counts.items():
            if signal != 'HOLD':
                print(f"  {signal}: {count}")
        print()

    # Create interactive chart
    print("Generating interactive chart...")
    title = f"Bitcoin {get_timeframe_description(args.timeframe)} - EMA Slope (SB:{args.smooth_bars}, MA:{args.ma_length}, NTZ:{args.ntz_threshold})"

    fig = create_combined_chart(
        df,
        ntz_threshold=args.ntz_threshold,
        title=title
    )

    # Save or display
    if args.output:
        output_file = args.output if args.output.endswith('.html') else f"{args.output}.html"
        fig.write_html(output_file)
        print(f"Chart saved to: {output_file}")
        print("\nOpen this file in a web browser to view the interactive chart.")
        print("You can:")
        print("  - Zoom by selecting a region")
        print("  - Pan by clicking and dragging")
        print("  - Reset view by double-clicking")
        print("  - Toggle traces by clicking the legend")
    else:
        print("Opening interactive chart in browser...")
        print("\nChart controls:")
        print("  - Zoom: Select a region with mouse")
        print("  - Pan: Click and drag")
        print("  - Reset: Double-click")
        print("  - Toggle: Click legend items")
        print("\nClose the browser tab when done.")
        fig.show()

    print()
    return 0


if __name__ == "__main__":
    sys.exit(main())
