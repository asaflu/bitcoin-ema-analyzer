"""
Binance API client with retry logic and rate limiting.
"""

import time
import requests
from typing import List, Optional
from retry import retry

from config import (
    BINANCE_KLINES_ENDPOINT,
    SYMBOL,
    INTERVAL,
    REQUEST_DELAY_MS,
    MAX_RETRIES,
    RETRY_BACKOFF_BASE,
    MAX_CANDLES_PER_REQUEST
)


class BinanceAPIError(Exception):
    """Custom exception for Binance API errors."""
    pass


class BinanceClient:
    """
    Client for fetching data from Binance public API.
    """

    def __init__(self, symbol: str = SYMBOL, interval: str = INTERVAL):
        """
        Initialize Binance API client.

        Args:
            symbol: Trading symbol (default: from config)
            interval: Candle interval (default: from config)
        """
        self.symbol = symbol
        self.interval = interval
        self.session = requests.Session()
        self.last_request_time = 0

    def _enforce_rate_limit(self):
        """
        Enforce rate limiting between API requests.
        Ensures minimum delay between consecutive requests.
        """
        current_time = time.time()
        time_since_last_request = (current_time - self.last_request_time) * 1000

        if time_since_last_request < REQUEST_DELAY_MS:
            sleep_time = (REQUEST_DELAY_MS - time_since_last_request) / 1000
            time.sleep(sleep_time)

        self.last_request_time = time.time()

    @retry(
        exceptions=(requests.RequestException, BinanceAPIError),
        tries=MAX_RETRIES,
        delay=RETRY_BACKOFF_BASE,
        backoff=2,
        jitter=(0, 1)
    )
    def fetch_klines(
        self,
        start_time: Optional[int] = None,
        end_time: Optional[int] = None,
        limit: int = MAX_CANDLES_PER_REQUEST
    ) -> List[List]:
        """
        Fetch kline/candlestick data from Binance API.

        Args:
            start_time: Start timestamp in milliseconds
            end_time: End timestamp in milliseconds
            limit: Number of candles to fetch (max 1000)

        Returns:
            List of kline data arrays

        Raises:
            BinanceAPIError: If API request fails
        """
        self._enforce_rate_limit()

        params = {
            "symbol": self.symbol,
            "interval": self.interval,
            "limit": min(limit, MAX_CANDLES_PER_REQUEST)
        }

        if start_time is not None:
            params["startTime"] = start_time

        if end_time is not None:
            params["endTime"] = end_time

        try:
            response = self.session.get(BINANCE_KLINES_ENDPOINT, params=params, timeout=30)

            # Handle rate limiting
            if response.status_code == 429:
                retry_after = int(response.headers.get("Retry-After", 60))
                raise BinanceAPIError(
                    f"Rate limit exceeded. Retry after {retry_after} seconds"
                )

            # Handle client errors (don't retry)
            if 400 <= response.status_code < 500:
                raise BinanceAPIError(
                    f"Client error {response.status_code}: {response.text}"
                )

            # Handle server errors (will retry)
            if response.status_code >= 500:
                raise BinanceAPIError(
                    f"Server error {response.status_code}: {response.text}"
                )

            response.raise_for_status()
            klines = response.json()

            return klines

        except requests.RequestException as e:
            raise BinanceAPIError(f"Request failed: {str(e)}")

    def get_earliest_valid_timestamp(self) -> int:
        """
        Get the earliest valid timestamp for the symbol.
        Fetches one candle to determine the earliest available data.

        Returns:
            Earliest valid timestamp in milliseconds
        """
        try:
            klines = self.fetch_klines(limit=1)
            if klines:
                return int(klines[0][0])
            raise BinanceAPIError("No data available from Binance")
        except Exception as e:
            raise BinanceAPIError(f"Failed to get earliest timestamp: {str(e)}")

    def get_latest_timestamp(self) -> int:
        """
        Get the most recent timestamp available from Binance.

        Returns:
            Latest timestamp in milliseconds
        """
        try:
            # Fetch most recent candle
            klines = self.fetch_klines(limit=1)
            if klines:
                # Return the close time of the most recent completed candle
                # We use close_time - 1 minute to get the start of the last completed candle
                return int(klines[0][0])
            raise BinanceAPIError("No data available from Binance")
        except Exception as e:
            raise BinanceAPIError(f"Failed to get latest timestamp: {str(e)}")
