"""
Advanced backtesting analytics and insights
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Tuple
import logging

logger = logging.getLogger(__name__)


class BacktestAnalyzer:
    """
    Analyze backtest results and generate insights.
    """

    def __init__(self, trades: pd.DataFrame, equity_curve: pd.DataFrame, initial_capital: float = 10000):
        """
        Initialize analyzer.

        Args:
            trades: DataFrame with trade history
            equity_curve: DataFrame with equity over time
            initial_capital: Starting capital
        """
        self.trades = trades
        self.equity_curve = equity_curve
        self.initial_capital = initial_capital

    def calculate_metrics(self) -> Dict[str, float]:
        """Calculate comprehensive performance metrics."""
        if len(self.trades) == 0:
            return self._empty_metrics()

        metrics = {}

        # Basic metrics
        metrics['total_trades'] = len(self.trades)
        metrics['winning_trades'] = len(self.trades[self.trades['pnl'] > 0])
        metrics['losing_trades'] = len(self.trades[self.trades['pnl'] < 0])
        metrics['win_rate'] = metrics['winning_trades'] / metrics['total_trades'] * 100 if metrics['total_trades'] > 0 else 0

        # PnL metrics
        metrics['total_pnl'] = self.trades['pnl'].sum()
        metrics['total_return_pct'] = (metrics['total_pnl'] / self.initial_capital) * 100
        metrics['avg_trade_pnl'] = self.trades['pnl'].mean()
        metrics['median_trade_pnl'] = self.trades['pnl'].median()

        # Win/Loss metrics
        winning_trades = self.trades[self.trades['pnl'] > 0]['pnl']
        losing_trades = self.trades[self.trades['pnl'] < 0]['pnl']

        metrics['avg_win'] = winning_trades.mean() if len(winning_trades) > 0 else 0
        metrics['avg_loss'] = losing_trades.mean() if len(losing_trades) > 0 else 0
        metrics['largest_win'] = winning_trades.max() if len(winning_trades) > 0 else 0
        metrics['largest_loss'] = losing_trades.min() if len(losing_trades) > 0 else 0

        # Risk metrics
        gross_profit = winning_trades.sum() if len(winning_trades) > 0 else 0
        gross_loss = abs(losing_trades.sum()) if len(losing_trades) > 0 else 0
        metrics['profit_factor'] = gross_profit / gross_loss if gross_loss > 0 else np.inf

        # Drawdown
        if 'equity' in self.equity_curve.columns:
            running_max = self.equity_curve['equity'].cummax()
            drawdown = (self.equity_curve['equity'] - running_max) / running_max * 100
            metrics['max_drawdown_pct'] = drawdown.min()
            metrics['avg_drawdown_pct'] = drawdown[drawdown < 0].mean() if len(drawdown[drawdown < 0]) > 0 else 0
        else:
            metrics['max_drawdown_pct'] = 0
            metrics['avg_drawdown_pct'] = 0

        # Sharpe ratio (annualized)
        if len(self.equity_curve) > 1 and 'equity' in self.equity_curve.columns:
            returns = self.equity_curve['equity'].pct_change().dropna()
            if len(returns) > 0 and returns.std() > 0:
                metrics['sharpe_ratio'] = np.sqrt(252) * returns.mean() / returns.std()
            else:
                metrics['sharpe_ratio'] = 0
        else:
            metrics['sharpe_ratio'] = 0

        # Trade duration metrics
        if 'entry_time' in self.trades.columns and 'exit_time' in self.trades.columns:
            self.trades['duration'] = pd.to_datetime(self.trades['exit_time']) - pd.to_datetime(self.trades['entry_time'])
            metrics['avg_trade_duration'] = self.trades['duration'].mean().total_seconds() / 3600  # hours
            metrics['median_trade_duration'] = self.trades['duration'].median().total_seconds() / 3600
        else:
            metrics['avg_trade_duration'] = 0
            metrics['median_trade_duration'] = 0

        # Consecutive wins/losses
        win_streak, loss_streak = self._calculate_streaks()
        metrics['max_consecutive_wins'] = win_streak
        metrics['max_consecutive_losses'] = loss_streak

        # Expectancy
        metrics['expectancy'] = (metrics['win_rate'] / 100 * metrics['avg_win']) + ((1 - metrics['win_rate'] / 100) * metrics['avg_loss'])

        return metrics

    def _empty_metrics(self) -> Dict[str, float]:
        """Return empty metrics when no trades."""
        return {
            'total_trades': 0,
            'winning_trades': 0,
            'losing_trades': 0,
            'win_rate': 0,
            'total_pnl': 0,
            'total_return_pct': 0,
            'avg_trade_pnl': 0,
            'median_trade_pnl': 0,
            'avg_win': 0,
            'avg_loss': 0,
            'largest_win': 0,
            'largest_loss': 0,
            'profit_factor': 0,
            'max_drawdown_pct': 0,
            'avg_drawdown_pct': 0,
            'sharpe_ratio': 0,
            'avg_trade_duration': 0,
            'median_trade_duration': 0,
            'max_consecutive_wins': 0,
            'max_consecutive_losses': 0,
            'expectancy': 0
        }

    def _calculate_streaks(self) -> Tuple[int, int]:
        """Calculate max consecutive wins and losses."""
        if len(self.trades) == 0:
            return 0, 0

        wins = (self.trades['pnl'] > 0).astype(int)
        max_win_streak = 0
        max_loss_streak = 0
        current_win_streak = 0
        current_loss_streak = 0

        for win in wins:
            if win:
                current_win_streak += 1
                current_loss_streak = 0
                max_win_streak = max(max_win_streak, current_win_streak)
            else:
                current_loss_streak += 1
                current_win_streak = 0
                max_loss_streak = max(max_loss_streak, current_loss_streak)

        return max_win_streak, max_loss_streak

    def generate_insights(self, metrics: Dict[str, float]) -> List[str]:
        """Generate textual insights from metrics."""
        insights = []

        # Performance assessment
        if metrics['total_return_pct'] > 50:
            insights.append(f"🎉 Excellent performance with {metrics['total_return_pct']:.1f}% total return")
        elif metrics['total_return_pct'] > 20:
            insights.append(f"✅ Good performance with {metrics['total_return_pct']:.1f}% total return")
        elif metrics['total_return_pct'] > 0:
            insights.append(f"📈 Positive return of {metrics['total_return_pct']:.1f}%")
        else:
            insights.append(f"⚠️ Negative return of {metrics['total_return_pct']:.1f}%")

        # Win rate analysis
        if metrics['win_rate'] > 60:
            insights.append(f"✨ High win rate of {metrics['win_rate']:.1f}%")
        elif metrics['win_rate'] < 40:
            insights.append(f"⚠️ Low win rate of {metrics['win_rate']:.1f}% - consider parameter adjustment")

        # Profit factor
        if metrics['profit_factor'] > 2:
            insights.append(f"💪 Strong profit factor of {metrics['profit_factor']:.2f}")
        elif metrics['profit_factor'] < 1:
            insights.append(f"❌ Profit factor below 1 ({metrics['profit_factor']:.2f}) - strategy is unprofitable")

        # Sharpe ratio
        if metrics['sharpe_ratio'] > 2:
            insights.append(f"🌟 Excellent risk-adjusted returns (Sharpe: {metrics['sharpe_ratio']:.2f})")
        elif metrics['sharpe_ratio'] > 1:
            insights.append(f"👍 Good risk-adjusted returns (Sharpe: {metrics['sharpe_ratio']:.2f})")
        elif metrics['sharpe_ratio'] < 0:
            insights.append(f"⚠️ Negative risk-adjusted returns (Sharpe: {metrics['sharpe_ratio']:.2f})")

        # Drawdown
        if abs(metrics['max_drawdown_pct']) > 30:
            insights.append(f"⚠️ High maximum drawdown of {abs(metrics['max_drawdown_pct']):.1f}% - consider risk management")
        elif abs(metrics['max_drawdown_pct']) > 20:
            insights.append(f"📊 Moderate drawdown of {abs(metrics['max_drawdown_pct']):.1f}%")
        else:
            insights.append(f"✅ Low drawdown of {abs(metrics['max_drawdown_pct']):.1f}%")

        # Trade frequency
        if metrics['total_trades'] < 10:
            insights.append(f"⚠️ Low trade frequency ({metrics['total_trades']} trades) - results may not be statistically significant")
        elif metrics['total_trades'] > 100:
            insights.append(f"✅ Good sample size with {metrics['total_trades']} trades")

        # Expectancy
        if metrics['expectancy'] > 0:
            insights.append(f"📈 Positive expectancy of ${metrics['expectancy']:.2f} per trade")
        else:
            insights.append(f"📉 Negative expectancy of ${metrics['expectancy']:.2f} per trade")

        return insights

    def generate_recommendations(self, metrics: Dict[str, float], param_comparison: pd.DataFrame = None) -> List[str]:
        """Generate actionable recommendations."""
        recommendations = []

        # Based on metrics
        if metrics['win_rate'] < 40 and abs(metrics['avg_loss']) > metrics['avg_win']:
            recommendations.append("Consider tightening stop losses or widening profit targets to improve win rate")

        if abs(metrics['max_drawdown_pct']) > 25:
            recommendations.append("High drawdown suggests adding position sizing rules or reducing leverage")

        if metrics['total_trades'] < 20:
            recommendations.append("Increase test period or adjust parameters to generate more trades for statistical significance")

        if metrics['profit_factor'] < 1.5:
            recommendations.append("Profit factor suggests strategy needs improvement - consider optimizing entry/exit rules")

        # Based on parameter comparison
        if param_comparison is not None and len(param_comparison) > 1:
            # Check if parameters show clear patterns
            if 'smooth_bars' in param_comparison.columns:
                best_smooth = param_comparison.iloc[0]['smooth_bars']
                recommendations.append(f"Best performing smooth_bars value: {best_smooth}")

            if 'ma_length' in param_comparison.columns:
                best_ma = param_comparison.iloc[0]['ma_length']
                recommendations.append(f"Optimal ma_length appears to be: {best_ma}")

            if 'ntz_threshold' in param_comparison.columns:
                best_ntz = param_comparison.iloc[0]['ntz_threshold']
                recommendations.append(f"Optimal NTZ threshold: {best_ntz}")

        return recommendations

    def get_trade_distribution(self) -> Dict[str, pd.DataFrame]:
        """Analyze trade distribution patterns."""
        if len(self.trades) == 0:
            return {}

        distribution = {}

        # PnL distribution
        distribution['pnl_histogram'] = self.trades['pnl'].describe()

        # Wins vs losses
        distribution['win_loss'] = pd.DataFrame({
            'count': [
                len(self.trades[self.trades['pnl'] > 0]),
                len(self.trades[self.trades['pnl'] < 0])
            ],
            'total_pnl': [
                self.trades[self.trades['pnl'] > 0]['pnl'].sum(),
                self.trades[self.trades['pnl'] < 0]['pnl'].sum()
            ]
        }, index=['Wins', 'Losses'])

        # Trade type distribution (if available)
        if 'type' in self.trades.columns:
            distribution['by_type'] = self.trades.groupby('type').agg({
                'pnl': ['count', 'sum', 'mean']
            })

        return distribution
