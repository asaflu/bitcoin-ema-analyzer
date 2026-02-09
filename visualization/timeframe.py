"""
Timeframe aggregation utilities
"""

import pandas as pd
import numpy as np


def resample_ohlcv(df, timeframe='5m'):
    """
    Resample 1-minute OHLCV data to different timeframes.

    Args:
        df: DataFrame with columns: timestamp, open, high, low, close, volume
        timeframe: Target timeframe ('1m', '5m', '15m', '30m', '1h', '2h', '4h', '1d', '1w')

    Returns:
        Resampled DataFrame
    """
    # Make a copy and ensure timestamp is datetime
    df = df.copy()

    if 'timestamp' in df.columns:
        df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
        df = df.set_index('timestamp')
    elif not isinstance(df.index, pd.DatetimeIndex):
        df.index = pd.to_datetime(df.index, unit='ms')

    # Mapping of timeframe strings to pandas offset aliases
    timeframe_map = {
        '1m': '1min',   # 1 minute
        '5m': '5min',   # 5 minutes
        '10m': '10min', # 10 minutes
        '15m': '15min', # 15 minutes
        '30m': '30min', # 30 minutes
        '1h': '1h',     # 1 hour
        '2h': '2h',     # 2 hours
        '4h': '4h',     # 4 hours
        '1d': '1D',     # 1 day
        '1w': '1W',     # 1 week
    }

    if timeframe not in timeframe_map:
        raise ValueError(f"Invalid timeframe: {timeframe}. Choose from: {list(timeframe_map.keys())}")

    freq = timeframe_map[timeframe]

    # Resample OHLCV data
    resampled = pd.DataFrame()

    # OHLC aggregation
    if 'open' in df.columns:
        resampled['open'] = df['open'].resample(freq).first()
    if 'high' in df.columns:
        resampled['high'] = df['high'].resample(freq).max()
    if 'low' in df.columns:
        resampled['low'] = df['low'].resample(freq).min()
    if 'close' in df.columns:
        resampled['close'] = df['close'].resample(freq).last()

    # Volume aggregation (sum)
    if 'volume' in df.columns:
        resampled['volume'] = df['volume'].resample(freq).sum()
    if 'quote_volume' in df.columns:
        resampled['quote_volume'] = df['quote_volume'].resample(freq).sum()
    if 'trades' in df.columns:
        resampled['trades'] = df['trades'].resample(freq).sum()
    if 'taker_buy_base' in df.columns:
        resampled['taker_buy_base'] = df['taker_buy_base'].resample(freq).sum()
    if 'taker_buy_quote' in df.columns:
        resampled['taker_buy_quote'] = df['taker_buy_quote'].resample(freq).sum()

    # Remove any rows with NaN in critical columns
    resampled = resampled.dropna(subset=['open', 'high', 'low', 'close'])

    # Reset index to have timestamp as column
    resampled = resampled.reset_index()

    # The index name is 'timestamp' from set_index(), so after reset_index()
    # the column is already named 'timestamp'

    # Convert timestamp back to milliseconds
    # DatetimeIndex.astype(np.int64) gives nanoseconds since epoch
    # Divide by 10**6 to get milliseconds
    if pd.api.types.is_datetime64_any_dtype(resampled['timestamp']):
        resampled['timestamp'] = (resampled['timestamp'].astype(np.int64) // 10**6).astype(np.int64)

    return resampled


def get_timeframe_description(timeframe):
    """Get human-readable description of timeframe"""
    descriptions = {
        '1m': '1 Minute',
        '5m': '5 Minutes',
        '10m': '10 Minutes',
        '15m': '15 Minutes',
        '30m': '30 Minutes',
        '1h': '1 Hour',
        '2h': '2 Hours',
        '4h': '4 Hours',
        '1d': '1 Day',
        '1w': '1 Week',
    }
    return descriptions.get(timeframe, timeframe)
