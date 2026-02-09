#!/usr/bin/env python3
"""
Test EMA Slope Trading Strategy
Parameters: smoothBars=3, maLength=9, NTZ threshold=10
"""

import sys
import pandas as pd
from datetime import datetime, timedelta

from database.connection import db
from database.queries import query_ohlcv_range, get_earliest_timestamp, get_latest_timestamp
from indicators.ema_slope import calculate_ema_slope
from backtesting.engine import BacktestEngine


def format_number(num):
    """Format number with commas"""
    return f"{num:,.2f}"


def main():
    print("=" * 70)
    print("EMA SLOPE TRADING STRATEGY BACKTEST")
    print("=" * 70)
    print(f"Parameters: smoothBars=3, maLength=9, NTZ threshold=10")
    print()

    # Get data from database
    print("Loading data from database...")
    with db.connection() as conn:
        earliest = get_earliest_timestamp(conn)
        latest = get_latest_timestamp(conn)

        print(f"Available data: {datetime.fromtimestamp(earliest/1000)} to {datetime.fromtimestamp(latest/1000)}")

        # For initial test, use last 3 months of data
        # Adjust this to test different periods
        test_start = latest - (90 * 24 * 60 * 60 * 1000)  # 90 days ago
        test_end = latest

        print(f"\nBacktest period: {datetime.fromtimestamp(test_start/1000)} to {datetime.fromtimestamp(test_end/1000)}")
        print("Fetching data...")

        data = query_ohlcv_range(conn, test_start, test_end)

    if not data:
        print("ERROR: No data found for specified period")
        return 1

    # Convert to DataFrame
    df = pd.DataFrame(data, columns=[
        'timestamp', 'open', 'high', 'low', 'close', 'volume',
        'quote_volume', 'trades', 'taker_buy_base', 'taker_buy_quote'
    ])

    print(f"Loaded {len(df):,} records")
    print()

    # Calculate EMA Slope indicator with specified parameters
    print("Calculating EMA Slope indicator...")
    df = calculate_ema_slope(
        df,
        smooth_bars=3,
        ma_length=9,
        ntz_threshold=10,
        ma_type='EMA',
        lookback=500
    )

    # Drop NaN values from indicator calculation
    df = df.dropna()
    print(f"Valid records after indicator calculation: {len(df):,}")
    print()

    # Show sample signals
    signal_counts = df['signal'].value_counts()
    print("Signal distribution:")
    for signal, count in signal_counts.items():
        print(f"  {signal}: {count:,}")
    print()

    # Run backtest
    print("Running backtest...")
    print("-" * 70)

    engine = BacktestEngine(
        initial_capital=10000,
        commission=0.001,  # 0.1% commission
        slippage=0.0005    # 0.05% slippage
    )

    results = engine.run_backtest(df, position_size=0.95)  # Use 95% of capital per trade

    # Display results
    if 'error' in results:
        print(f"ERROR: {results['error']}")
        return 1

    print("\nBACKTEST RESULTS")
    print("=" * 70)
    print(f"Initial Capital:        ${format_number(results['initial_capital'])}")
    print(f"Final Equity:           ${format_number(results['final_equity'])}")
    print(f"Total Return:           {results['total_return']:.2f}%")
    print(f"Max Drawdown:           {results['max_drawdown']:.2f}%")
    print(f"Sharpe Ratio:           {results['sharpe_ratio']:.2f}")
    print()

    print("TRADE STATISTICS")
    print("-" * 70)
    print(f"Total Trades:           {results['total_trades']}")
    print(f"Winning Trades:         {results['winning_trades']} ({results['win_rate']:.1f}%)")
    print(f"Losing Trades:          {results['losing_trades']}")
    print(f"Win Rate:               {results['win_rate']:.2f}%")
    print()

    print(f"Average Win:            ${format_number(results['avg_win'])}")
    print(f"Average Loss:           ${format_number(results['avg_loss'])}")
    print(f"Largest Win:            ${format_number(results['largest_win'])}")
    print(f"Largest Loss:           ${format_number(results['largest_loss'])}")
    print(f"Profit Factor:          {results['profit_factor']:.2f}")
    print()

    # Show recent trades
    print("RECENT TRADES (Last 10)")
    print("-" * 70)
    trades_df = results['trades_df']
    sell_trades = trades_df[trades_df['type'] == 'SELL'].tail(10)

    if len(sell_trades) > 0:
        for _, trade in sell_trades.iterrows():
            ts = pd.to_datetime(trade['timestamp'], unit='ms')
            profit_pct = trade.get('profit_pct', 0)
            profit = trade.get('profit', 0)
            print(f"{ts}: ${trade['price']:.2f} | "
                  f"Profit: ${profit:.2f} ({profit_pct:+.2f}%)")

    print()
    print("=" * 70)
    print("Backtest completed successfully!")
    print()

    # Save results to CSV
    print("Saving detailed results...")
    trades_df.to_csv('backtest_trades.csv', index=False)
    results['equity_df'].to_csv('backtest_equity_curve.csv', index=False)
    print("  - backtest_trades.csv")
    print("  - backtest_equity_curve.csv")
    print()

    return 0


if __name__ == "__main__":
    sys.exit(main())
