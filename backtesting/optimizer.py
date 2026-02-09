"""
Parameter optimization framework for backtesting
Supports grid search and parallel execution
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Tuple, Callable, Any
from itertools import product
from concurrent.futures import ProcessPoolExecutor, as_completed
from tqdm import tqdm
import logging

logger = logging.getLogger(__name__)


class ParameterOptimizer:
    """
    Optimize strategy parameters using grid search.
    """

    def __init__(self, strategy_function: Callable, metric: str = 'sharpe_ratio'):
        """
        Initialize optimizer.

        Args:
            strategy_function: Function that takes params and returns results
            metric: Metric to optimize ('sharpe_ratio', 'total_return', 'win_rate', etc.)
        """
        self.strategy_function = strategy_function
        self.metric = metric
        self.results = []

    def grid_search(
        self,
        param_grid: Dict[str, List[Any]],
        data: pd.DataFrame,
        n_jobs: int = 1,
        show_progress: bool = True
    ) -> pd.DataFrame:
        """
        Perform grid search over parameter space.

        Args:
            param_grid: Dictionary of parameter names to list of values
            data: Data to backtest on
            n_jobs: Number of parallel jobs (1 = sequential)
            show_progress: Show progress bar

        Returns:
            DataFrame with results for each parameter combination
        """
        # Generate all parameter combinations
        param_names = list(param_grid.keys())
        param_values = list(param_grid.values())
        combinations = list(product(*param_values))

        logger.info(f"Testing {len(combinations)} parameter combinations")

        results = []

        if n_jobs == 1:
            # Sequential execution
            iterator = tqdm(combinations, desc="Grid Search") if show_progress else combinations
            for combo in iterator:
                params = dict(zip(param_names, combo))
                try:
                    result = self.strategy_function(data, **params)
                    result['params'] = params
                    results.append(result)
                except Exception as e:
                    logger.error(f"Error with params {params}: {e}")
                    continue
        else:
            # Parallel execution
            with ProcessPoolExecutor(max_workers=n_jobs) as executor:
                futures = {
                    executor.submit(self.strategy_function, data, **dict(zip(param_names, combo))): combo
                    for combo in combinations
                }

                iterator = tqdm(as_completed(futures), total=len(futures), desc="Grid Search") if show_progress else as_completed(futures)
                for future in iterator:
                    combo = futures[future]
                    try:
                        result = future.result()
                        result['params'] = dict(zip(param_names, combo))
                        results.append(result)
                    except Exception as e:
                        params = dict(zip(param_names, combo))
                        logger.error(f"Error with params {params}: {e}")
                        continue

        # Convert to DataFrame
        results_df = pd.DataFrame(results)

        # Extract parameter columns
        if len(results_df) > 0 and 'params' in results_df.columns:
            param_df = pd.json_normalize(results_df['params'])
            results_df = pd.concat([results_df.drop('params', axis=1), param_df], axis=1)

        # Sort by optimization metric
        if self.metric in results_df.columns:
            results_df = results_df.sort_values(self.metric, ascending=False)

        self.results = results_df
        return results_df

    def get_best_params(self) -> Dict[str, Any]:
        """Get best parameter combination."""
        if len(self.results) == 0:
            return {}

        best_row = self.results.iloc[0]
        # Only return basic parameter columns, not results or dataframes
        param_cols = [col for col in self.results.columns if col not in [
            'total_return', 'sharpe_ratio', 'win_rate', 'profit_factor',
            'max_drawdown', 'total_trades', 'avg_trade', 'best_trade', 'worst_trade',
            'equity_curve', 'trades', 'full_metrics'
        ]]
        return {col: best_row[col] for col in param_cols}

    def get_top_n(self, n: int = 10) -> pd.DataFrame:
        """Get top N parameter combinations."""
        return self.results.head(n)


def compare_timeframes(
    strategy_function: Callable,
    timeframes: List[str],
    data_loader: Callable,
    fixed_params: Dict[str, Any],
    date_range: Tuple[str, str]
) -> pd.DataFrame:
    """
    Compare strategy performance across different timeframes.

    Args:
        strategy_function: Strategy function to test
        timeframes: List of timeframes to test
        data_loader: Function to load data for each timeframe
        fixed_params: Fixed strategy parameters
        date_range: (start_date, end_date) tuple

    Returns:
        DataFrame comparing results across timeframes
    """
    results = []

    for tf in tqdm(timeframes, desc="Testing Timeframes"):
        try:
            # Load data for this timeframe
            data = data_loader(tf, date_range)

            # Run strategy
            result = strategy_function(data, **fixed_params)
            result['timeframe'] = tf

            results.append(result)
        except Exception as e:
            logger.error(f"Error testing timeframe {tf}: {e}")
            continue

    return pd.DataFrame(results)


def walk_forward_analysis(
    strategy_function: Callable,
    data: pd.DataFrame,
    param_grid: Dict[str, List[Any]],
    train_size: int,
    test_size: int,
    metric: str = 'sharpe_ratio'
) -> Dict[str, Any]:
    """
    Perform walk-forward optimization.

    Args:
        strategy_function: Strategy to test
        data: Full dataset
        param_grid: Parameters to optimize
        train_size: Training window size (in rows)
        test_size: Testing window size (in rows)
        metric: Metric to optimize

    Returns:
        Dictionary with walk-forward results
    """
    optimizer = ParameterOptimizer(strategy_function, metric=metric)

    n_windows = (len(data) - train_size) // test_size
    all_results = []

    for i in range(n_windows):
        train_start = i * test_size
        train_end = train_start + train_size
        test_start = train_end
        test_end = test_start + test_size

        if test_end > len(data):
            break

        # Training data
        train_data = data.iloc[train_start:train_end]

        # Optimize on training data
        train_results = optimizer.grid_search(param_grid, train_data, show_progress=False)
        best_params = optimizer.get_best_params()

        # Test on out-of-sample data
        test_data = data.iloc[test_start:test_end]
        test_result = strategy_function(test_data, **best_params)

        all_results.append({
            'window': i,
            'train_start': train_start,
            'train_end': train_end,
            'test_start': test_start,
            'test_end': test_end,
            'best_params': best_params,
            'test_result': test_result
        })

    return {
        'windows': all_results,
        'avg_test_return': np.mean([r['test_result']['total_return'] for r in all_results]),
        'avg_test_sharpe': np.mean([r['test_result']['sharpe_ratio'] for r in all_results]),
    }
