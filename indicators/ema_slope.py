"""
EMA Slope Indicator Implementation
Based on Pine Script by Pedro Braconnot
"""

import numpy as np
import pandas as pd


def ema(series, length):
    """Calculate Exponential Moving Average"""
    return series.ewm(span=length, adjust=False).mean()


def sma(series, length):
    """Calculate Simple Moving Average"""
    return series.rolling(window=length).mean()


def wma(series, length):
    """Calculate Weighted Moving Average"""
    weights = np.arange(1, length + 1)
    return series.rolling(window=length).apply(
        lambda x: np.dot(x, weights) / weights.sum(), raw=True
    )


def dema(series, length):
    """Calculate Double Exponential Moving Average"""
    e = ema(series, length)
    return 2 * e - ema(e, length)


def tema(series, length):
    """Calculate Triple Exponential Moving Average"""
    e = ema(series, length)
    return 3 * (e - ema(e, length)) + ema(ema(e, length), length)


def hma(series, length):
    """Calculate Hull Moving Average"""
    half_length = int(length / 2)
    sqrt_length = int(np.sqrt(length))
    return wma(2 * wma(series, half_length) - wma(series, length), sqrt_length)


def calculate_ma(series, ma_type='EMA', length=120):
    """
    Calculate moving average based on type.

    Args:
        series: Price series (usually close prices)
        ma_type: Type of MA ('SMA', 'EMA', 'DEMA', 'TEMA', 'WMA', 'HMA')
        length: MA length period

    Returns:
        pandas Series with MA values
    """
    if ma_type == 'SMA':
        return sma(series, length)
    elif ma_type == 'EMA':
        return ema(series, length)
    elif ma_type == 'DEMA':
        return dema(series, length)
    elif ma_type == 'TEMA':
        return tema(series, length)
    elif ma_type == 'WMA':
        return wma(series, length)
    elif ma_type == 'HMA':
        return hma(series, length)
    else:
        raise ValueError(f"Unknown MA type: {ma_type}")


def calculate_ema_slope(df, smooth_bars=3, ma_length=120, ntz_threshold=10,
                        ma_type='EMA', lookback=500):
    """
    Calculate EMA Slope indicator.

    Args:
        df: DataFrame with OHLCV data (must have 'close' column)
        smooth_bars: Number of bars for slope smoothing
        ma_length: Moving average length
        ntz_threshold: No Trade Zone threshold (±)
        ma_type: Type of moving average
        lookback: Lookback period for normalization

    Returns:
        DataFrame with additional columns:
            - ma: Moving average values
            - ma_diff: Raw MA difference
            - slope: Normalized slope (-100 to 100)
            - acceleration: Slope acceleration
            - in_ntz: Boolean - True if in No Trade Zone
            - signal: Trade signal ('BUY', 'SELL', 'HOLD')
    """
    result = df.copy()

    # Calculate moving average
    result['ma'] = calculate_ma(result['close'], ma_type, ma_length)

    # Calculate raw MA difference (slope)
    result['ma_diff'] = result['ma'] - result['ma'].shift(smooth_bars)

    # Normalize slope to -100 to 100 scale
    # Use expanding window for first 'lookback' periods to avoid NaN values
    result['ma_diff_max'] = result['ma_diff'].rolling(window=lookback, min_periods=1).max()
    result['ma_diff_min'] = result['ma_diff'].rolling(window=lookback, min_periods=1).min()
    ma_range = result['ma_diff_max'] - result['ma_diff_min']

    # Avoid division by zero
    ma_range = ma_range.replace(0, np.nan)
    result['slope'] = 100 * result['ma_diff'] / ma_range

    # Calculate acceleration
    slope_change = abs(result['slope'] - result['slope'].shift(1)) * smooth_bars * 2
    accel_high = slope_change.rolling(window=200, min_periods=1).max()
    accel_high = accel_high.replace(0, np.nan)
    result['acceleration'] = 50 * slope_change / accel_high

    # Determine if in No Trade Zone
    result['in_ntz'] = (result['slope'].abs() <= ntz_threshold)

    # Generate trading signals with position state tracking
    # Ensure only one position can be open at a time
    result['signal'] = 'HOLD'

    position = 'FLAT'  # Track current position state: FLAT, LONG, or SHORT

    for i in range(1, len(result)):
        current_slope = result['slope'].iloc[i]
        prev_slope = result['slope'].iloc[i-1]

        if pd.isna(current_slope) or pd.isna(prev_slope):
            result.iloc[i, result.columns.get_loc('signal')] = 'HOLD'
            continue

        # State machine for position management
        if position == 'FLAT':
            # Can open LONG: slope crosses above +ntz_threshold
            if current_slope > ntz_threshold and prev_slope <= ntz_threshold:
                result.iloc[i, result.columns.get_loc('signal')] = 'BUY'
                position = 'LONG'
            # Can open SHORT: slope crosses below -ntz_threshold
            elif current_slope < -ntz_threshold and prev_slope >= -ntz_threshold:
                result.iloc[i, result.columns.get_loc('signal')] = 'SELL'
                position = 'SHORT'

        elif position == 'LONG':
            # Must exit LONG: slope crosses back below +ntz_threshold
            if current_slope < ntz_threshold and prev_slope >= ntz_threshold:
                result.iloc[i, result.columns.get_loc('signal')] = 'EXIT_LONG'
                position = 'FLAT'

        elif position == 'SHORT':
            # Must exit SHORT: slope crosses back above -ntz_threshold
            if current_slope > -ntz_threshold and prev_slope <= -ntz_threshold:
                result.iloc[i, result.columns.get_loc('signal')] = 'EXIT_SHORT'
                position = 'FLAT'

    # Clean up intermediate columns
    result = result.drop(['ma_diff_max', 'ma_diff_min'], axis=1)

    # Forward fill NaN values in slope (for initial periods)
    result['slope'] = result['slope'].bfill().fillna(0)
    result['acceleration'] = result['acceleration'].fillna(0)
    result['in_ntz'] = result['in_ntz'].fillna(True)

    return result


def get_signal_state(slope, slope_prev, ntz_threshold):
    """
    Determine the current signal state.

    Returns: 'BULLISH', 'BEARISH', 'NTZ' (No Trade Zone)
    """
    if slope > ntz_threshold:
        return 'BULLISH'
    elif slope < -ntz_threshold:
        return 'BEARISH'
    else:
        return 'NTZ'
