"""
HTML report generator for backtest results
Creates comprehensive, interactive reports with charts
"""

import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import plotly.express as px
from datetime import datetime
from typing import Dict, List
import json


class HTMLReportGenerator:
    """Generate comprehensive HTML reports for backtest results."""

    def __init__(self, title: str = "Backtest Report"):
        """Initialize report generator."""
        self.title = title
        self.sections = []

    def generate_report(
        self,
        metrics: Dict[str, float],
        trades: pd.DataFrame,
        equity_curve: pd.DataFrame,
        insights: List[str],
        recommendations: List[str],
        param_results: pd.DataFrame = None,
        timeframe_results: pd.DataFrame = None,
        output_file: str = "backtest_report.html"
    ):
        """
        Generate complete HTML report.

        Args:
            metrics: Performance metrics dictionary
            trades: Trade history DataFrame
            equity_curve: Equity curve DataFrame
            insights: List of insight strings
            recommendations: List of recommendation strings
            param_results: Parameter optimization results
            timeframe_results: Timeframe comparison results
            output_file: Output HTML file path
        """
        html_parts = []

        # Header
        html_parts.append(self._generate_header())

        # Summary section
        html_parts.append(self._generate_summary(metrics, insights))

        # Key metrics cards
        html_parts.append(self._generate_metrics_cards(metrics))

        # Equity curve
        if len(equity_curve) > 0:
            html_parts.append(self._generate_equity_chart(equity_curve))

        # Trade distribution
        if len(trades) > 0:
            html_parts.append(self._generate_trade_distribution(trades))

        # Drawdown analysis
        if len(equity_curve) > 0:
            html_parts.append(self._generate_drawdown_chart(equity_curve))

        # Parameter optimization results
        if param_results is not None and len(param_results) > 0:
            html_parts.append(self._generate_parameter_analysis(param_results))

        # Timeframe comparison
        if timeframe_results is not None and len(timeframe_results) > 0:
            html_parts.append(self._generate_timeframe_comparison(timeframe_results))

        # Recommendations
        if recommendations:
            html_parts.append(self._generate_recommendations(recommendations))

        # Trade table
        if len(trades) > 0:
            html_parts.append(self._generate_trade_table(trades))

        # Footer
        html_parts.append(self._generate_footer())

        # Combine and save
        full_html = '\n'.join(html_parts)
        with open(output_file, 'w') as f:
            f.write(full_html)

        return output_file

    def _generate_header(self) -> str:
        """Generate HTML header with styles."""
        return f"""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{self.title}</title>
    <script src="https://cdn.plot.ly/plotly-2.27.0.min.js"></script>
    <link rel="stylesheet" href="https://cdn.datatables.net/1.13.7/css/jquery.dataTables.min.css">
    <script src="https://code.jquery.com/jquery-3.7.1.min.js"></script>
    <script src="https://cdn.datatables.net/1.13.7/js/jquery.dataTables.min.js"></script>
    <style>
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, Cantarell, sans-serif;
            margin: 0;
            padding: 20px;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
        }}
        .container {{
            max-width: 1400px;
            margin: 0 auto;
            background: white;
            border-radius: 20px;
            box-shadow: 0 20px 60px rgba(0,0,0,0.3);
            overflow: hidden;
        }}
        .header {{
            background: linear-gradient(135deg, #1e3c72 0%, #2a5298 100%);
            color: white;
            padding: 40px;
            text-align: center;
        }}
        .header h1 {{
            margin: 0;
            font-size: 2.5em;
            font-weight: 700;
        }}
        .header p {{
            margin: 10px 0 0 0;
            opacity: 0.9;
            font-size: 1.1em;
        }}
        .section {{
            padding: 40px;
            border-bottom: 1px solid #e0e0e0;
        }}
        .section:last-child {{
            border-bottom: none;
        }}
        .section-title {{
            font-size: 1.8em;
            font-weight: 600;
            margin-bottom: 20px;
            color: #1e3c72;
        }}
        .metrics-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
            gap: 20px;
            margin: 20px 0;
        }}
        .metric-card {{
            background: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%);
            padding: 25px;
            border-radius: 15px;
            box-shadow: 0 4px 6px rgba(0,0,0,0.1);
            transition: transform 0.3s;
        }}
        .metric-card:hover {{
            transform: translateY(-5px);
            box-shadow: 0 8px 12px rgba(0,0,0,0.15);
        }}
        .metric-label {{
            font-size: 0.9em;
            color: #666;
            margin-bottom: 8px;
            font-weight: 500;
        }}
        .metric-value {{
            font-size: 2em;
            font-weight: 700;
            color: #1e3c72;
        }}
        .metric-value.positive {{
            color: #10b981;
        }}
        .metric-value.negative {{
            color: #ef4444;
        }}
        .insight-box {{
            background: #f0f9ff;
            border-left: 4px solid #3b82f6;
            padding: 15px 20px;
            margin: 10px 0;
            border-radius: 8px;
        }}
        .recommendation-box {{
            background: #fef3c7;
            border-left: 4px solid #f59e0b;
            padding: 15px 20px;
            margin: 10px 0;
            border-radius: 8px;
        }}
        .chart-container {{
            margin: 30px 0;
            background: white;
            border-radius: 15px;
            padding: 20px;
            box-shadow: 0 2px 8px rgba(0,0,0,0.1);
        }}
        table.dataframe, table.display {{
            width: 100%;
            border-collapse: collapse;
            margin: 20px 0;
            font-size: 0.9em;
        }}
        table.dataframe th, table.display th {{
            background: #1e3c72;
            color: white;
            padding: 12px;
            text-align: left;
            font-weight: 600;
        }}
        table.dataframe td, table.display td {{
            padding: 10px;
            border-bottom: 1px solid #e0e0e0;
        }}
        table.dataframe tr:hover, table.display tbody tr:hover {{
            background: #f5f5f5;
        }}
        .positive {{
            color: #10b981;
            font-weight: 600;
        }}
        .negative {{
            color: #ef4444;
            font-weight: 600;
        }}
        .text-right {{
            text-align: right;
        }}
        .dataTables_wrapper .dataTables_filter input {{
            border: 1px solid #ddd;
            border-radius: 4px;
            padding: 5px 10px;
            margin-left: 8px;
        }}
        .dataTables_wrapper .dataTables_length select {{
            border: 1px solid #ddd;
            border-radius: 4px;
            padding: 5px;
            margin: 0 5px;
        }}
        .footer {{
            background: #f5f5f5;
            padding: 30px;
            text-align: center;
            color: #666;
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>{self.title}</h1>
            <p>Generated on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
        </div>
"""

    def _generate_summary(self, metrics: Dict[str, float], insights: List[str]) -> str:
        """Generate summary section."""
        html = '<div class="section">'
        html += '<div class="section-title">📊 Executive Summary</div>'

        for insight in insights:
            html += f'<div class="insight-box">{insight}</div>'

        html += '</div>'
        return html

    def _generate_metrics_cards(self, metrics: Dict[str, float]) -> str:
        """Generate metric cards."""
        html = '<div class="section">'
        html += '<div class="section-title">📈 Key Performance Indicators</div>'
        html += '<div class="metrics-grid">'

        # Define key metrics to display
        key_metrics = [
            ('Total Return', f"{metrics.get('total_return_pct', 0):.2f}%", metrics.get('total_return_pct', 0) > 0),
            ('Win Rate', f"{metrics.get('win_rate', 0):.1f}%", metrics.get('win_rate', 0) > 50),
            ('Profit Factor', f"{metrics.get('profit_factor', 0):.2f}", metrics.get('profit_factor', 0) > 1),
            ('Sharpe Ratio', f"{metrics.get('sharpe_ratio', 0):.2f}", metrics.get('sharpe_ratio', 0) > 0),
            ('Max Drawdown', f"{abs(metrics.get('max_drawdown_pct', 0)):.1f}%", metrics.get('max_drawdown_pct', 0) > -20),
            ('Total Trades', f"{int(metrics.get('total_trades', 0))}", True),
            ('Avg Win', f"${metrics.get('avg_win', 0):.2f}", True),
            ('Avg Loss', f"${metrics.get('avg_loss', 0):.2f}", False),
        ]

        for label, value, is_positive in key_metrics:
            color_class = 'positive' if is_positive else 'negative'
            html += f'''
                <div class="metric-card">
                    <div class="metric-label">{label}</div>
                    <div class="metric-value {color_class}">{value}</div>
                </div>
            '''

        html += '</div></div>'
        return html

    def _generate_equity_chart(self, equity_curve: pd.DataFrame) -> str:
        """Generate equity curve chart."""
        fig = go.Figure()

        fig.add_trace(go.Scatter(
            x=equity_curve.index if 'timestamp' not in equity_curve.columns else equity_curve['timestamp'],
            y=equity_curve['equity'],
            mode='lines',
            name='Equity',
            line=dict(color='#3b82f6', width=2),
            fill='tozeroy',
            fillcolor='rgba(59, 130, 246, 0.1)'
        ))

        fig.update_layout(
            title='Equity Curve',
            xaxis_title='Time',
            yaxis_title='Equity ($)',
            template='plotly_white',
            height=400,
            hovermode='x unified'
        )

        chart_html = fig.to_html(include_plotlyjs=False, div_id='equity_chart')

        return f'''
        <div class="section">
            <div class="section-title">💰 Equity Curve</div>
            <div class="chart-container">
                {chart_html}
            </div>
        </div>
        '''

    def _generate_trade_distribution(self, trades: pd.DataFrame) -> str:
        """Generate trade distribution charts."""
        fig = make_subplots(
            rows=1, cols=2,
            subplot_titles=('PnL Distribution', 'Wins vs Losses'),
            specs=[[{'type': 'histogram'}, {'type': 'pie'}]]
        )

        # PnL histogram
        fig.add_trace(
            go.Histogram(
                x=trades['pnl'],
                nbinsx=30,
                name='PnL',
                marker_color='#3b82f6'
            ),
            row=1, col=1
        )

        # Wins vs Losses pie
        wins = len(trades[trades['pnl'] > 0])
        losses = len(trades[trades['pnl'] <= 0])

        fig.add_trace(
            go.Pie(
                labels=['Wins', 'Losses'],
                values=[wins, losses],
                marker_colors=['#10b981', '#ef4444']
            ),
            row=1, col=2
        )

        fig.update_layout(height=400, template='plotly_white', showlegend=False)

        chart_html = fig.to_html(include_plotlyjs=False, div_id='trade_dist')

        return f'''
        <div class="section">
            <div class="section-title">📊 Trade Distribution</div>
            <div class="chart-container">
                {chart_html}
            </div>
        </div>
        '''

    def _generate_drawdown_chart(self, equity_curve: pd.DataFrame) -> str:
        """Generate drawdown chart."""
        if 'equity' not in equity_curve.columns:
            return ""

        running_max = equity_curve['equity'].cummax()
        drawdown = (equity_curve['equity'] - running_max) / running_max * 100

        fig = go.Figure()

        fig.add_trace(go.Scatter(
            x=equity_curve.index if 'timestamp' not in equity_curve.columns else equity_curve['timestamp'],
            y=drawdown,
            mode='lines',
            name='Drawdown',
            line=dict(color='#ef4444', width=2),
            fill='tozeroy',
            fillcolor='rgba(239, 68, 68, 0.1)'
        ))

        fig.update_layout(
            title='Drawdown Over Time',
            xaxis_title='Time',
            yaxis_title='Drawdown (%)',
            template='plotly_white',
            height=300,
            hovermode='x unified'
        )

        chart_html = fig.to_html(include_plotlyjs=False, div_id='drawdown_chart')

        return f'''
        <div class="section">
            <div class="section-title">📉 Drawdown Analysis</div>
            <div class="chart-container">
                {chart_html}
            </div>
        </div>
        '''

    def _generate_parameter_analysis(self, param_results: pd.DataFrame) -> str:
        """Generate parameter optimization results."""
        # Top 10 parameter combinations
        top_params = param_results.head(10).copy()

        # Create config labels with parameter descriptions
        config_labels = []
        for i, row in top_params.iterrows():
            params_str = f"SB:{int(row.get('smooth_bars', 0))}, MA:{int(row.get('ma_length', 0))}, NTZ:{int(row.get('ntz_threshold', 0))}"
            config_labels.append(f"Config {i+1}<br><small>{params_str}</small>")

        # Create bar chart of top results
        fig = go.Figure()

        metric_col = 'sharpe_ratio' if 'sharpe_ratio' in top_params.columns else 'total_return'

        fig.add_trace(go.Bar(
            x=config_labels,
            y=top_params[metric_col],
            marker_color='#3b82f6',
            text=top_params[metric_col].round(2),
            textposition='outside',
            hovertemplate='<b>%{x}</b><br>' + metric_col.replace('_', ' ').title() + ': %{y:.2f}<extra></extra>'
        ))

        fig.update_layout(
            title=f'Top 10 Parameter Combinations by {metric_col.replace("_", " ").title()}',
            xaxis_title='Configuration (Smooth Bars, MA Length, NTZ Threshold)',
            yaxis_title=metric_col.replace('_', ' ').title(),
            template='plotly_white',
            height=500,
            margin=dict(b=120)
        )

        chart_html = fig.to_html(include_plotlyjs=False, div_id='param_chart')

        # Prepare clean table data
        display_cols = ['smooth_bars', 'ma_length', 'ntz_threshold', 'sharpe_ratio',
                       'total_return', 'win_rate', 'profit_factor', 'max_drawdown', 'total_trades']

        # Filter to only existing columns
        display_cols = [col for col in display_cols if col in top_params.columns]

        table_data = top_params[display_cols].copy()

        # Format numeric columns
        if 'sharpe_ratio' in table_data.columns:
            table_data['sharpe_ratio'] = table_data['sharpe_ratio'].round(2)
        if 'total_return' in table_data.columns:
            table_data['total_return'] = table_data['total_return'].round(2).astype(str) + '%'
        if 'win_rate' in table_data.columns:
            table_data['win_rate'] = table_data['win_rate'].round(1).astype(str) + '%'
        if 'profit_factor' in table_data.columns:
            table_data['profit_factor'] = table_data['profit_factor'].round(2)
        if 'max_drawdown' in table_data.columns:
            table_data['max_drawdown'] = table_data['max_drawdown'].round(1).astype(str) + '%'

        # Rename columns for display
        table_data.columns = [col.replace('_', ' ').title() for col in table_data.columns]

        # Add config number
        table_data.insert(0, 'Rank', range(1, len(table_data) + 1))

        table_html = table_data.to_html(index=False, table_id='param_table', classes='display', escape=False)

        return f'''
        <div class="section">
            <div class="section-title">🎯 Parameter Optimization Results</div>
            <p style="color: #666; margin-bottom: 20px;">
                Testing {len(param_results)} parameter combinations.
                <strong>SB</strong> = Smooth Bars, <strong>MA</strong> = MA Length, <strong>NTZ</strong> = No Trade Zone Threshold
            </p>
            <div class="chart-container">
                {chart_html}
            </div>
            <div style="margin-top: 30px; overflow-x: auto;">
                <h3 style="margin-bottom: 15px;">📊 Top 10 Configurations (Sortable)</h3>
                {table_html}
            </div>
            <script>
                $(document).ready(function() {{
                    $('#param_table').DataTable({{
                        order: [[1, 'asc']],
                        pageLength: 10,
                        searching: true,
                        info: true
                    }});
                }});
            </script>
        </div>
        '''

    def _generate_timeframe_comparison(self, timeframe_results: pd.DataFrame) -> str:
        """Generate timeframe comparison charts."""
        fig = make_subplots(
            rows=2, cols=2,
            subplot_titles=('Total Return by Timeframe', 'Sharpe Ratio', 'Win Rate', 'Max Drawdown'),
            specs=[[{'type': 'bar'}, {'type': 'bar'}],
                   [{'type': 'bar'}, {'type': 'bar'}]]
        )

        # Total return
        fig.add_trace(
            go.Bar(x=timeframe_results['timeframe'], y=timeframe_results['total_return'], marker_color='#3b82f6'),
            row=1, col=1
        )

        # Sharpe ratio
        fig.add_trace(
            go.Bar(x=timeframe_results['timeframe'], y=timeframe_results['sharpe_ratio'], marker_color='#10b981'),
            row=1, col=2
        )

        # Win rate
        fig.add_trace(
            go.Bar(x=timeframe_results['timeframe'], y=timeframe_results['win_rate'], marker_color='#f59e0b'),
            row=2, col=1
        )

        # Max drawdown
        fig.add_trace(
            go.Bar(x=timeframe_results['timeframe'], y=timeframe_results['max_drawdown'], marker_color='#ef4444'),
            row=2, col=2
        )

        fig.update_layout(height=600, template='plotly_white', showlegend=False)

        chart_html = fig.to_html(include_plotlyjs=False, div_id='timeframe_chart')

        return f'''
        <div class="section">
            <div class="section-title">⏱️ Timeframe Comparison</div>
            <div class="chart-container">
                {chart_html}
            </div>
        </div>
        '''

    def _generate_recommendations(self, recommendations: List[str]) -> str:
        """Generate recommendations section."""
        html = '<div class="section">'
        html += '<div class="section-title">💡 Recommendations</div>'

        for rec in recommendations:
            html += f'<div class="recommendation-box">✨ {rec}</div>'

        html += '</div>'
        return html

    def _generate_trade_table(self, trades: pd.DataFrame, max_rows: int = 100) -> str:
        """Generate trade history table."""
        if len(trades) == 0:
            return ""

        display_trades = trades.copy()

        # Format timestamps to readable dates
        if 'entry_time' in display_trades.columns:
            display_trades['entry_time'] = pd.to_datetime(display_trades['entry_time'], unit='ms').dt.strftime('%Y-%m-%d %H:%M')
        if 'exit_time' in display_trades.columns:
            display_trades['exit_time'] = pd.to_datetime(display_trades['exit_time'], unit='ms').dt.strftime('%Y-%m-%d %H:%M')

        # Format numeric columns
        if 'pnl' in display_trades.columns:
            display_trades['pnl'] = display_trades['pnl'].round(2)
        if 'entry_price' in display_trades.columns:
            display_trades['entry_price'] = display_trades['entry_price'].round(2)
        if 'exit_price' in display_trades.columns:
            display_trades['exit_price'] = display_trades['exit_price'].round(2)

        # Calculate return %
        if 'entry_price' in display_trades.columns and 'exit_price' in display_trades.columns:
            display_trades['return_%'] = ((display_trades['exit_price'] / display_trades['entry_price'] - 1) * 100).round(2)

        # Select and rename columns for display
        display_cols = []
        col_mapping = {
            'entry_time': 'Entry Time',
            'exit_time': 'Exit Time',
            'type': 'Type',
            'entry_price': 'Entry Price',
            'exit_price': 'Exit Price',
            'pnl': 'P&L ($)',
            'return_%': 'Return (%)'
        }

        for col, new_name in col_mapping.items():
            if col in display_trades.columns:
                display_cols.append(col)

        display_trades = display_trades[display_cols]
        display_trades.columns = [col_mapping[col] for col in display_cols]

        # Add trade number
        display_trades.insert(0, '#', range(1, len(display_trades) + 1))

        # Take only first max_rows
        if len(display_trades) > max_rows:
            display_trades = display_trades.head(max_rows)

        table_html = display_trades.to_html(index=False, table_id='trade_table', classes='display', escape=False)

        return f'''
        <div class="section">
            <div class="section-title">📋 Trade History</div>
            <p style="color: #666; margin-bottom: 20px;">
                Showing {min(max_rows, len(trades))} of {len(trades)} total trades.
                Click column headers to sort. Use search box to filter.
            </p>
            <div style="overflow-x: auto;">
                {table_html}
            </div>
            <script>
                $(document).ready(function() {{
                    $('#trade_table').DataTable({{
                        order: [[0, 'asc']],
                        pageLength: 25,
                        searching: true,
                        info: true,
                        columnDefs: [
                            {{ targets: [5, 6], className: 'text-right' }}
                        ]
                    }});
                }});
            </script>
        </div>
        '''

    def _generate_footer(self) -> str:
        """Generate HTML footer."""
        return '''
        <div class="footer">
            <p>Generated by Bitcoin EMA Slope Backtesting Engine</p>
            <p>📈 Trade responsibly • Past performance does not guarantee future results</p>
        </div>
    </div>
</body>
</html>
'''
