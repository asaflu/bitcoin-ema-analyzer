"""
Backtesting Engine for Trading Strategies
"""

import pandas as pd
import numpy as np
from datetime import datetime


class BacktestEngine:
    """
    Simple backtesting engine for testing trading strategies.
    """

    def __init__(self, initial_capital=10000, commission=0.001, slippage=0.0005):
        """
        Initialize backtesting engine.

        Args:
            initial_capital: Starting capital in USD
            commission: Commission rate (0.001 = 0.1%)
            slippage: Slippage rate (0.0005 = 0.05%)
        """
        self.initial_capital = initial_capital
        self.commission = commission
        self.slippage = slippage
        self.reset()

    def reset(self):
        """Reset the backtest state"""
        self.capital = self.initial_capital
        self.position = 0  # Number of BTC held
        self.position_value = 0  # Value of position in USD
        self.trades = []
        self.equity_curve = []
        self.in_position = False
        self.entry_price = 0
        self.entry_time = None

    def execute_trade(self, timestamp, price, signal, position_size=1.0):
        """
        Execute a trade based on signal.

        Args:
            timestamp: Trade timestamp
            price: Current price
            signal: Trade signal ('BUY', 'SELL', 'EXIT_LONG', 'EXIT_SHORT', 'HOLD')
            position_size: Fraction of capital to use (0-1)
        """
        if signal == 'BUY' and not self.in_position:
            # Enter long position
            buy_price = price * (1 + self.slippage)
            position_cost = self.capital * position_size
            commission_cost = position_cost * self.commission

            self.position = (position_cost - commission_cost) / buy_price
            self.capital -= position_cost
            self.position_value = self.position * price
            self.in_position = True
            self.entry_price = buy_price
            self.entry_time = timestamp

            self.trades.append({
                'timestamp': timestamp,
                'type': 'BUY',
                'price': buy_price,
                'quantity': self.position,
                'cost': position_cost,
                'commission': commission_cost,
                'capital': self.capital,
                'position_value': self.position_value
            })

        elif (signal in ['SELL', 'EXIT_LONG']) and self.in_position:
            # Exit long position
            sell_price = price * (1 - self.slippage)
            position_value = self.position * sell_price
            commission_cost = position_value * self.commission

            profit = position_value - (self.position * self.entry_price)
            profit_pct = (sell_price / self.entry_price - 1) * 100

            self.capital += position_value - commission_cost
            self.position = 0
            self.position_value = 0
            self.in_position = False

            self.trades.append({
                'timestamp': timestamp,
                'type': 'SELL',
                'price': sell_price,
                'quantity': self.position,
                'value': position_value,
                'commission': commission_cost,
                'capital': self.capital,
                'profit': profit,
                'profit_pct': profit_pct,
                'entry_price': self.entry_price,
                'entry_time': self.entry_time,
                'hold_duration': timestamp - self.entry_time if self.entry_time else None
            })

            self.entry_price = 0
            self.entry_time = None

    def update_equity(self, timestamp, price):
        """Update equity curve"""
        total_equity = self.capital
        if self.in_position:
            total_equity += self.position * price

        self.equity_curve.append({
            'timestamp': timestamp,
            'equity': total_equity,
            'capital': self.capital,
            'position_value': self.position * price if self.in_position else 0,
            'in_position': self.in_position
        })

    def run_backtest(self, df, position_size=1.0):
        """
        Run backtest on DataFrame with signals.

        Args:
            df: DataFrame with 'close' and 'signal' columns
            position_size: Fraction of capital to use per trade (0-1)

        Returns:
            Dictionary with backtest results
        """
        self.reset()

        for idx, row in df.iterrows():
            timestamp = row['timestamp'] if 'timestamp' in row else idx
            price = row['close']
            signal = row.get('signal', 'HOLD')

            # Execute trade if there's a signal
            if signal in ['BUY', 'SELL', 'EXIT_LONG', 'EXIT_SHORT']:
                self.execute_trade(timestamp, price, signal, position_size)

            # Update equity curve
            self.update_equity(timestamp, price)

        # Close any open position at the end
        if self.in_position:
            last_row = df.iloc[-1]
            timestamp = last_row['timestamp'] if 'timestamp' in last_row else df.index[-1]
            self.execute_trade(timestamp, last_row['close'], 'SELL', position_size)

        return self.get_performance_metrics()

    def get_performance_metrics(self):
        """Calculate performance metrics"""
        if not self.trades or len(self.equity_curve) == 0:
            return {
                'error': 'No trades executed',
                'total_trades': 0
            }

        trades_df = pd.DataFrame(self.trades)
        equity_df = pd.DataFrame(self.equity_curve)

        # Filter to sell trades only for P&L analysis
        sell_trades = trades_df[trades_df['type'] == 'SELL'].copy()

        if len(sell_trades) == 0:
            return {
                'error': 'No completed trades',
                'total_trades': 0
            }

        # Calculate metrics
        final_equity = equity_df['equity'].iloc[-1]
        total_return = ((final_equity / self.initial_capital) - 1) * 100

        # Trade statistics
        winning_trades = sell_trades[sell_trades['profit'] > 0]
        losing_trades = sell_trades[sell_trades['profit'] <= 0]

        total_trades = len(sell_trades)
        win_rate = (len(winning_trades) / total_trades * 100) if total_trades > 0 else 0

        avg_win = winning_trades['profit'].mean() if len(winning_trades) > 0 else 0
        avg_loss = losing_trades['profit'].mean() if len(losing_trades) > 0 else 0

        profit_factor = (
            abs(winning_trades['profit'].sum() / losing_trades['profit'].sum())
            if len(losing_trades) > 0 and losing_trades['profit'].sum() != 0
            else float('inf') if len(winning_trades) > 0 else 0
        )

        # Drawdown calculation
        equity_df['peak'] = equity_df['equity'].cummax()
        equity_df['drawdown'] = (equity_df['equity'] - equity_df['peak']) / equity_df['peak'] * 100
        max_drawdown = equity_df['drawdown'].min()

        # Sharpe ratio (simplified, assuming risk-free rate = 0)
        returns = equity_df['equity'].pct_change().dropna()
        sharpe_ratio = (
            np.sqrt(252) * returns.mean() / returns.std()
            if len(returns) > 0 and returns.std() != 0 else 0
        )

        return {
            'initial_capital': self.initial_capital,
            'final_equity': final_equity,
            'total_return': total_return,
            'total_return_pct': total_return,
            'total_trades': total_trades,
            'winning_trades': len(winning_trades),
            'losing_trades': len(losing_trades),
            'win_rate': win_rate,
            'avg_win': avg_win,
            'avg_loss': avg_loss,
            'largest_win': winning_trades['profit'].max() if len(winning_trades) > 0 else 0,
            'largest_loss': losing_trades['profit'].min() if len(losing_trades) > 0 else 0,
            'profit_factor': profit_factor,
            'max_drawdown': max_drawdown,
            'sharpe_ratio': sharpe_ratio,
            'trades_df': trades_df,
            'equity_df': equity_df
        }
