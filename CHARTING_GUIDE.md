# Interactive Bitcoin Charting Guide

## EMA Slope Indicator Implementation

The EMA Slope indicator has been fully implemented based on the Pine Script you provided, with parameters:
- **smoothBars**: 3
- **maLength**: 9
- **NTZ threshold**: 10

## Quick Start

### Generate Interactive Charts

```bash
# Activate virtual environment
source venv/bin/activate

# 1-hour chart (last 30 days)
python interactive_chart.py --timeframe 1h --days 30

# 5-minute chart (last 3 days)
python interactive_chart.py --timeframe 5m --days 3

# 4-hour chart (last 90 days)
python interactive_chart.py --timeframe 4h --days 90

# 1-day chart (last year)
python interactive_chart.py --timeframe 1d --days 365
```

## Available Timeframes

- **1m** - 1 Minute
- **5m** - 5 Minutes
- **10m** - 10 Minutes
- **15m** - 15 Minutes
- **30m** - 30 Minutes
- **1h** - 1 Hour
- **2h** - 2 Hours
- **4h** - 4 Hours
- **1d** - 1 Day
- **1w** - 1 Week

## Command Line Options

```bash
python interactive_chart.py [OPTIONS]

Options:
  -t, --timeframe     Timeframe (default: 1h)
                      Choices: 1m, 5m, 10m, 15m, 30m, 1h, 2h, 4h, 1d, 1w

  -d, --days          Number of days to display (default: 7)

  --smooth-bars       EMA Slope smooth bars (default: 3)

  --ma-length         EMA length (default: 9)

  --ntz-threshold     No Trade Zone threshold (default: 10)

  -o, --output        Save to HTML file instead of opening browser
```

## Examples

### Custom Parameters

```bash
# Test different EMA lengths
python interactive_chart.py -t 1h -d 30 --ma-length 20

# Adjust NTZ threshold
python interactive_chart.py -t 4h -d 60 --ntz-threshold 15

# Different smooth bars
python interactive_chart.py -t 1d -d 365 --smooth-bars 5
```

### Save to HTML

```bash
# Generate and save chart
python interactive_chart.py -t 1h -d 30 -o my_chart.html

# Open the HTML file in your browser
open my_chart.html  # Mac
# or
xdg-open my_chart.html  # Linux
# or just double-click the file
```

## Chart Features

### Interactive Controls

- **Zoom In**: Click and drag to select a region
- **Pan**: Click and drag on the chart
- **Reset View**: Double-click anywhere on the chart
- **Toggle Indicators**: Click legend items to show/hide
- **Hover Data**: Hover over candles for detailed OHLCV info

### Chart Components

1. **Top Panel**: Price chart with candlesticks
   - Green candles = price up
   - Red candles = price down
   - Yellow line = EMA
   - Green triangles = Buy signals
   - Red triangles = Sell signals

2. **Middle Panel**: Volume
   - Green bars = buying volume
   - Red bars = selling volume

3. **Bottom Panel**: EMA Slope Indicator
   - White line = Slope value
   - Green zone (above +10) = Bullish momentum
   - Red zone (below -10) = Bearish momentum
   - Gray zone (-10 to +10) = No Trade Zone (NTZ)

## Understanding the EMA Slope Indicator

### Signal Types

- **BUY**: Slope crosses above NTZ threshold (+10)
  - Indicates start of bullish momentum
  - Price trend is strengthening upward

- **SELL**: Slope crosses below NTZ threshold (-10)
  - Indicates start of bearish momentum
  - Price trend is strengthening downward

- **EXIT_LONG**: Slope enters NTZ from above
  - Bullish momentum is weakening
  - Consider taking profits on long positions

- **EXIT_SHORT**: Slope enters NTZ from below
  - Bearish momentum is weakening
  - Consider taking profits on short positions

- **HOLD** (NTZ): Slope is within ±10
  - No clear trend direction
  - Choppy/sideways market - avoid trading

### Trading Strategy

1. **Entry**:
   - Buy when slope breaks above +10 (BUY signal)
   - Sell/Short when slope breaks below -10 (SELL signal)

2. **Exit**:
   - Exit longs when slope enters NTZ from above
   - Exit shorts when slope enters NTZ from below

3. **Avoid**:
   - Don't trade when slope is in NTZ (-10 to +10)
   - Wait for clear momentum signals

## Generated Charts

The system has generated several example charts:

- `bitcoin_chart_5m.html` - 5-minute chart (3 days)
- `bitcoin_chart_1h.html` - 1-hour chart (30 days)
- `bitcoin_chart_4h.html` - 4-hour chart (90 days)
- `bitcoin_chart_1d.html` - 1-day chart (1 year)

Open any of these HTML files in your web browser to explore the interactive charts.

## Backtesting

To backtest a trading strategy with these parameters:

```bash
python test_ema_slope_strategy.py
```

This will run a backtest on the last 90 days of data and generate:
- Performance metrics (win rate, profit factor, Sharpe ratio)
- Trade history
- Equity curve

Output files:
- `backtest_trades.csv` - Detailed trade log
- `backtest_equity_curve.csv` - Equity over time

## Tips for Different Timeframes

### Scalping (1m, 5m)
- More signals, more noise
- Best for: Day trading, quick moves
- Recommended days: 1-7

### Swing Trading (1h, 4h)
- Balanced signal frequency
- Best for: Position trading, catching swings
- Recommended days: 30-90

### Position Trading (1d, 1w)
- Fewer but stronger signals
- Best for: Long-term trends
- Recommended days: 180-365

## Next Steps

1. **Explore Charts**: Open the generated HTML files
2. **Test Parameters**: Try different ma-length and ntz-threshold values
3. **Run Backtest**: Test the strategy's historical performance
4. **Optimize**: Find the best parameters for your trading style

## Technical Details

### Data Source
- All data comes from the local SQLite database
- Original resolution: 1-minute candles
- Automatic aggregation to requested timeframe

### Indicator Calculation
- EMA calculated using pandas exponential weighted mean
- Slope normalized to -100 to +100 scale
- Acceleration shows rate of slope change

### Performance
- Chart generation: ~1-2 seconds for most timeframes
- Interactive: Smooth 60 FPS with WebGL acceleration
- Data capacity: Millions of data points
