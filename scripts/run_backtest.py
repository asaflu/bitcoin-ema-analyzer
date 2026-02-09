#!/usr/bin/env python3
"""
Comprehensive backtesting script for EMA Slope strategy
Tests multiple timeframes and parameters, generates HTML reports
"""

import sys
import os
from datetime import datetime, timedelta
import pandas as pd
import numpy as np

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from database.connection import db
from database.queries import query_ohlcv_range, get_latest_timestamp
from indicators.ema_slope import calculate_ema_slope
from visualization.timeframe import resample_ohlcv
from backtesting.engine import BacktestEngine
from backtesting.optimizer import ParameterOptimizer, compare_timeframes
from backtesting.analyzer import BacktestAnalyzer
from backtesting.report_generator import HTMLReportGenerator
from utils.logger import setup_logger

logger = setup_logger('backtest')


def load_data_for_timeframe(timeframe: str, years: int = 3):
    """Load data for a specific timeframe."""
    with db.connection() as conn:
        latest_ms = get_latest_timestamp(conn)
        start_ms = latest_ms - (years * 365 * 24 * 60 * 60 * 1000)

        data = query_ohlcv_range(conn, start_ms, latest_ms)

    if not data:
        raise ValueError(f"No data found for timeframe {timeframe}")

    df = pd.DataFrame(data, columns=[
        'timestamp', 'open', 'high', 'low', 'close', 'volume',
        'quote_volume', 'trades', 'taker_buy_base', 'taker_buy_quote'
    ])

    # Resample if not 1m
    if timeframe != '1m':
        df = resample_ohlcv(df, timeframe)

    return df


def run_strategy(data, smooth_bars=3, ma_length=9, ntz_threshold=10, commission=0.001, slippage=0.0005):
    """
    Run EMA Slope strategy on data.

    Returns dict with performance metrics.
    """
    # Calculate indicator
    lookback = min(500, len(data) // 2)
    df = calculate_ema_slope(
        data.copy(),
        smooth_bars=smooth_bars,
        ma_length=ma_length,
        ntz_threshold=ntz_threshold,
        ma_type='EMA',
        lookback=lookback
    )

    # Drop NaN values
    df = df.dropna(subset=['close', 'slope', 'signal'])

    if len(df) == 0:
        return {
            'total_return': 0,
            'sharpe_ratio': 0,
            'win_rate': 0,
            'profit_factor': 0,
            'max_drawdown': 0,
            'total_trades': 0,
            'avg_trade': 0,
            'best_trade': 0,
            'worst_trade': 0
        }

    # Run backtest
    engine = BacktestEngine(
        initial_capital=10000,
        commission=commission,
        slippage=slippage
    )

    result = engine.run_backtest(df)

    # Check if backtest failed
    if 'error' in result:
        return {
            'total_return': 0,
            'sharpe_ratio': 0,
            'win_rate': 0,
            'profit_factor': 0,
            'max_drawdown': 0,
            'total_trades': 0,
            'avg_trade': 0,
            'best_trade': 0,
            'worst_trade': 0
        }

    trades = result['trades_df']
    equity_curve = result['equity_df']

    # Filter to sell trades for analysis
    sell_trades = trades[trades['type'] == 'SELL'].copy()

    # Create trade DataFrame for analyzer
    if len(sell_trades) > 0:
        analyzer_trades = pd.DataFrame({
            'entry_time': sell_trades['entry_time'],
            'exit_time': sell_trades['timestamp'],
            'entry_price': sell_trades['entry_price'],
            'exit_price': sell_trades['price'],
            'pnl': sell_trades['profit'],
            'type': 'LONG'
        })
    else:
        analyzer_trades = pd.DataFrame()

    # Analyze results
    analyzer = BacktestAnalyzer(analyzer_trades, equity_curve, initial_capital=10000)
    metrics = analyzer.calculate_metrics()

    return {
        'total_return': metrics['total_return_pct'],
        'sharpe_ratio': metrics['sharpe_ratio'],
        'win_rate': metrics['win_rate'],
        'profit_factor': metrics['profit_factor'],
        'max_drawdown': metrics['max_drawdown_pct'],
        'total_trades': metrics['total_trades'],
        'avg_trade': metrics['avg_trade_pnl'],
        'best_trade': metrics['largest_win'],
        'worst_trade': metrics['largest_loss'],
        'equity_curve': equity_curve,
        'trades': analyzer_trades,
        'full_metrics': metrics
    }


def main():
    logger.info("=" * 70)
    logger.info("COMPREHENSIVE BACKTEST - EMA SLOPE STRATEGY")
    logger.info("=" * 70)

    # Configuration
    years_back = 3
    timeframes = ['5m', '15m', '30m', '1h', '2h', '4h', '1d']

    # Parameter grid for optimization
    param_grid = {
        'smooth_bars': [1, 2, 3, 4, 5],
        'ma_length': [5, 7, 9, 12, 15, 20],
        'ntz_threshold': [5, 8, 10, 12, 15]
    }

    logger.info(f"Testing period: Last {years_back} years")
    logger.info(f"Timeframes: {', '.join(timeframes)}")
    logger.info(f"Parameter combinations: {len(param_grid['smooth_bars']) * len(param_grid['ma_length']) * len(param_grid['ntz_threshold'])}")
    logger.info("")

    # ========== PART 1: Timeframe Comparison (with default params) ==========
    logger.info("PART 1: Comparing timeframes with default parameters...")
    logger.info("-" * 70)

    default_params = {'smooth_bars': 3, 'ma_length': 9, 'ntz_threshold': 10}
    timeframe_results = []

    for tf in timeframes:
        logger.info(f"Testing {tf} timeframe...")
        try:
            data = load_data_for_timeframe(tf, years_back)
            result = run_strategy(data, **default_params)

            timeframe_results.append({
                'timeframe': tf,
                'total_return': result['total_return'],
                'sharpe_ratio': result['sharpe_ratio'],
                'win_rate': result['win_rate'],
                'profit_factor': result['profit_factor'],
                'max_drawdown': result['max_drawdown'],
                'total_trades': result['total_trades']
            })

            logger.info(f"  Return: {result['total_return']:.2f}% | Sharpe: {result['sharpe_ratio']:.2f} | Trades: {result['total_trades']}")
        except Exception as e:
            logger.error(f"  Error testing {tf}: {e}")

    timeframe_df = pd.DataFrame(timeframe_results)
    timeframe_df = timeframe_df.sort_values('sharpe_ratio', ascending=False)

    logger.info("")
    logger.info("Best performing timeframes (by Sharpe ratio):")
    for i, row in timeframe_df.head(3).iterrows():
        logger.info(f"  {row['timeframe']}: Sharpe={row['sharpe_ratio']:.2f}, Return={row['total_return']:.2f}%")

    # ========== PART 2: Parameter Optimization on Best Timeframe ==========
    logger.info("")
    logger.info("PART 2: Optimizing parameters on best timeframe...")
    logger.info("-" * 70)

    best_timeframe = timeframe_df.iloc[0]['timeframe']
    logger.info(f"Best timeframe: {best_timeframe}")
    logger.info(f"Loading data for parameter optimization...")

    best_tf_data = load_data_for_timeframe(best_timeframe, years_back)

    optimizer = ParameterOptimizer(run_strategy, metric='sharpe_ratio')
    param_results = optimizer.grid_search(param_grid, best_tf_data, n_jobs=1, show_progress=True)

    logger.info("")
    logger.info("Top 5 parameter combinations:")
    for i, row in param_results.head(5).iterrows():
        logger.info(f"  #{i+1}: smooth_bars={row['smooth_bars']}, ma_length={row['ma_length']}, ntz_threshold={row['ntz_threshold']}")
        logger.info(f"      Sharpe={row['sharpe_ratio']:.2f}, Return={row['total_return']:.2f}%, Win Rate={row['win_rate']:.1f}%")

    # ========== PART 3: Full Backtest with Best Parameters ==========
    logger.info("")
    logger.info("PART 3: Running full backtest with optimal parameters...")
    logger.info("-" * 70)

    best_params = optimizer.get_best_params()
    logger.info(f"Best parameters: {best_params}")

    final_result = run_strategy(best_tf_data, **best_params)
    final_metrics = final_result['full_metrics']
    final_trades = final_result['trades']
    final_equity = final_result['equity_curve']

    logger.info(f"Final Performance:")
    logger.info(f"  Total Return: {final_metrics['total_return_pct']:.2f}%")
    logger.info(f"  Sharpe Ratio: {final_metrics['sharpe_ratio']:.2f}")
    logger.info(f"  Win Rate: {final_metrics['win_rate']:.1f}%")
    logger.info(f"  Profit Factor: {final_metrics['profit_factor']:.2f}")
    logger.info(f"  Max Drawdown: {abs(final_metrics['max_drawdown_pct']):.1f}%")
    logger.info(f"  Total Trades: {final_metrics['total_trades']}")

    # ========== PART 4: Generate HTML Report ==========
    logger.info("")
    logger.info("PART 4: Generating comprehensive HTML report...")
    logger.info("-" * 70)

    analyzer = BacktestAnalyzer(final_trades, final_equity, initial_capital=10000)
    insights = analyzer.generate_insights(final_metrics)
    recommendations = analyzer.generate_recommendations(final_metrics, param_results)

    report_gen = HTMLReportGenerator(title="EMA Slope Strategy - Comprehensive Backtest Report")

    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    output_file = f"backtest_report_{timestamp}.html"

    report_gen.generate_report(
        metrics=final_metrics,
        trades=final_trades,
        equity_curve=final_equity,
        insights=insights,
        recommendations=recommendations,
        param_results=param_results,
        timeframe_results=timeframe_df,
        output_file=output_file
    )

    logger.info(f"Report saved to: {output_file}")
    logger.info("")
    logger.info("=" * 70)
    logger.info("BACKTEST COMPLETE")
    logger.info("=" * 70)

    return 0


if __name__ == "__main__":
    sys.exit(main())
