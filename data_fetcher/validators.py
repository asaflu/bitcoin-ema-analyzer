"""
OHLCV data validation functions.
"""

from typing import List, Tuple, Optional


class ValidationError(Exception):
    """Custom exception for data validation errors."""
    pass


def validate_ohlcv_record(record: Tuple) -> bool:
    """
    Validate a single OHLCV record for data integrity.

    Args:
        record: Tuple (timestamp, open, high, low, close, volume,
                quote_volume, trades, taker_buy_base, taker_buy_quote)

    Returns:
        True if valid

    Raises:
        ValidationError: If validation fails
    """
    if len(record) != 10:
        raise ValidationError(f"Expected 10 fields, got {len(record)}")

    timestamp, open_, high, low, close, volume, quote_volume, trades, taker_buy_base, taker_buy_quote = record

    # Validate timestamp
    if not isinstance(timestamp, (int, float)) or timestamp <= 0:
        raise ValidationError(f"Invalid timestamp: {timestamp}")

    # Validate OHLC relationships
    if not (high >= open_ and high >= close and high >= low):
        raise ValidationError(
            f"High price constraint violated: high={high}, open={open_}, "
            f"close={close}, low={low}"
        )

    if not (low <= open_ and low <= close and low <= high):
        raise ValidationError(
            f"Low price constraint violated: low={low}, open={open_}, "
            f"close={close}, high={high}"
        )

    # Validate volumes
    if volume < 0:
        raise ValidationError(f"Volume cannot be negative: {volume}")

    if quote_volume < 0:
        raise ValidationError(f"Quote volume cannot be negative: {quote_volume}")

    # Validate trades
    if not isinstance(trades, (int, float)) or trades < 0:
        raise ValidationError(f"Invalid trades count: {trades}")

    # Validate taker buy volumes
    if taker_buy_base < 0:
        raise ValidationError(f"Taker buy base cannot be negative: {taker_buy_base}")

    if taker_buy_quote < 0:
        raise ValidationError(f"Taker buy quote cannot be negative: {taker_buy_quote}")

    return True


def validate_ohlcv_batch(records: List[Tuple]) -> Tuple[List[Tuple], List[str]]:
    """
    Validate a batch of OHLCV records.

    Args:
        records: List of OHLCV record tuples

    Returns:
        Tuple of (valid_records, error_messages)
    """
    valid_records = []
    errors = []

    for i, record in enumerate(records):
        try:
            if validate_ohlcv_record(record):
                valid_records.append(record)
        except ValidationError as e:
            errors.append(f"Record {i}: {str(e)}")

    return valid_records, errors


def validate_timestamp_continuity(
    records: List[Tuple],
    interval_ms: int = 60000,
    tolerance_ms: int = 1000
) -> List[str]:
    """
    Validate that timestamps are in chronological order and continuous.

    Args:
        records: List of OHLCV record tuples
        interval_ms: Expected interval between records in milliseconds
        tolerance_ms: Allowed tolerance for timestamp differences

    Returns:
        List of warning messages (empty if all valid)
    """
    warnings = []

    if not records:
        return warnings

    # Check chronological order
    prev_timestamp = None
    for i, record in enumerate(records):
        timestamp = record[0]

        if prev_timestamp is not None:
            if timestamp <= prev_timestamp:
                warnings.append(
                    f"Timestamp out of order at index {i}: "
                    f"prev={prev_timestamp}, current={timestamp}"
                )
            else:
                # Check continuity (allowing for small gaps)
                expected_diff = interval_ms
                actual_diff = timestamp - prev_timestamp

                if abs(actual_diff - expected_diff) > tolerance_ms:
                    warnings.append(
                        f"Gap detected at index {i}: expected {expected_diff}ms, "
                        f"got {actual_diff}ms between {prev_timestamp} and {timestamp}"
                    )

        prev_timestamp = timestamp

    return warnings


def parse_binance_kline(kline: List) -> Tuple:
    """
    Parse Binance kline data into OHLCV record tuple.

    Binance kline format:
    [
        open_time, open, high, low, close, volume,
        close_time, quote_asset_volume, number_of_trades,
        taker_buy_base_asset_volume, taker_buy_quote_asset_volume, ignore
    ]

    Args:
        kline: Raw kline data from Binance API

    Returns:
        Tuple (timestamp, open, high, low, close, volume,
               quote_volume, trades, taker_buy_base, taker_buy_quote)
    """
    return (
        int(kline[0]),      # timestamp (open_time)
        float(kline[1]),    # open
        float(kline[2]),    # high
        float(kline[3]),    # low
        float(kline[4]),    # close
        float(kline[5]),    # volume
        float(kline[7]),    # quote_volume
        int(kline[8]),      # trades
        float(kline[9]),    # taker_buy_base
        float(kline[10])    # taker_buy_quote
    )
