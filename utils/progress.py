"""
Progress tracking with tqdm integration.
"""

from tqdm import tqdm
from typing import Optional
from datetime import datetime


class ProgressTracker:
    """
    Progress tracker for data fetching operations.
    """

    def __init__(self, total: int, desc: str = "Fetching data"):
        """
        Initialize progress tracker.

        Args:
            total: Total number of items to process
            desc: Description for progress bar
        """
        self.total = total
        self.desc = desc
        self.pbar: Optional[tqdm] = None
        self.current = 0

    def __enter__(self):
        """Start progress tracking."""
        self.pbar = tqdm(
            total=self.total,
            desc=self.desc,
            unit="batch",
            bar_format="{l_bar}{bar}| {n_fmt}/{total_fmt} [{elapsed}<{remaining}]"
        )
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Clean up progress tracker."""
        if self.pbar:
            self.pbar.close()

    def update(self, n: int = 1, **kwargs):
        """
        Update progress.

        Args:
            n: Number of items processed
            **kwargs: Additional fields to display (e.g., timestamp)
        """
        if self.pbar:
            self.current += n

            # Update postfix with additional info
            if kwargs:
                postfix_str = ", ".join(f"{k}={v}" for k, v in kwargs.items())
                self.pbar.set_postfix_str(postfix_str)

            self.pbar.update(n)

    def set_description(self, desc: str):
        """Update description."""
        if self.pbar:
            self.pbar.set_description(desc)


def format_timestamp(timestamp_ms: int) -> str:
    """
    Format timestamp for display.

    Args:
        timestamp_ms: Timestamp in milliseconds

    Returns:
        Formatted datetime string
    """
    dt = datetime.fromtimestamp(timestamp_ms / 1000)
    return dt.strftime("%Y-%m-%d %H:%M")
