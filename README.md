# Weather Trading System for Kalshi Markets

A Python system for trading Kalshi weather markets (KXHIGHNY) based on weather forecast data. Built for the probability & statistics class championship.

## Overview

This system:
- Fetches weather forecasts from multiple sources (Open-Meteo, NWS)
- Calculates consensus predictions
- Identifies the best Kalshi market to trade
- Tracks performance over time

## Quick Start

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Make Today's Trading Decision

```bash
python live_trader.py
```

This will:
- Fetch forecasts from multiple sources
- Calculate a consensus temperature
- Identify which market to trade on Kalshi
- Log the decision to `trades.json`

### 3. Track Performance

```bash
python track_performance.py
```

This will:
- Check results of past trades
- Calculate win rate
- Show profitability estimates

## Files

### Core System
- `live_trader.py` - Main trading system (run daily at 9 AM your time)
- `track_performance.py` - Performance tracking and statistics
- `data_fetchers.py` - Data fetching utilities
- `trades.json` - Log of all trades (auto-generated)

### Testing/Research
- `backtest.py` - Historical backtesting (limited by data availability)
- `test_*.py` - Various data source tests

## How It Works

### 1. Weather Forecast Sources

**Open-Meteo** (Free)
- Global weather model data
- Good baseline forecast

**NWS/Weather.gov** (Free)
- US National Weather Service
- Official US government forecasts
- Often very accurate for US locations

**OpenWeatherMap** (Optional, requires API key)
- Additional forecast source
- Free tier: 1000 calls/day
- Get API key at: https://openweathermap.org/api

### 2. Consensus Algorithm

The system:
1. Fetches forecasts from multiple sources
2. Calculates weighted average
3. Computes confidence based on agreement between sources
4. Higher confidence = sources agree more

### 3. Market Selection

Based on consensus forecast, selects the Kalshi market bucket:
- "57° or below"
- "57° to 58°"
- "58° to 59°"
- etc.

### 4. Trading Strategy

**Optimal trading time**: 9 AM UTC+3 (your timezone)
- Markets typically priced 40-50¢ at this time
- Best value before market efficiency increases

## Championship Strategy

### Daily Routine

**Every morning at 9 AM (your time):**

1. Run the trader:
```bash
python live_trader.py
```

2. Review the recommendation:
   - Consensus forecast
   - Market to trade
   - Confidence level

3. Execute on Kalshi:
   - Go to the recommended market
   - Buy "Yes" contracts
   - Target entry: 40-50¢ per contract

4. Track next day:
```bash
python track_performance.py
```

### Advanced: Intraday Updates

For bonus points, you can update positions during the day:

```bash
# Run again around 2 PM
python live_trader.py

# Compare to morning decision
# If forecast changed significantly, consider adjusting
```

## Market Information

### KXHIGHNY Markets

- **Series**: Highest temperature in NYC
- **Frequency**: Daily
- **Markets per day**: ~6 buckets
- **Settlement source**: NWS Climate Report (https://forecast.weather.gov/product.php?site=OKX&product=CLI&issuedby=NYC)
- **Close time**: ~4 AM EST next day
- **Settlement**: Based on max temp reported by NWS for Central Park

### Market Types

1. **Tail markets**: "X° or above", "Y° or below"
2. **Bucket markets**: "X° to Y°" (1-degree ranges)

## Performance Metrics

The championship ranks by:
1. **Number of wins** (primary metric)
2. Profitability (secondary)

### Win Rate Analysis

Random guessing: ~16.7% (1 in 6 markets)

Your target: >30% win rate
- Above 40% = very good
- Above 50% = excellent

### Expected Performance

Based on preliminary testing:
- **Forecast error**: ~1.5°F average
- **Challenge**: 1.5°F error can shift between buckets
- **Solution**: Multiple forecasts + consensus reduces error

## Limitations & Challenges

### Historical Backtesting

The main challenge we encountered: true historical forecast data is hard to find.

- Open-Meteo's "historical forecast" API doesn't provide real archived forecasts
- Visual Crossing has real data but costs $35/month
- Limited ability to backtest strategies accurately

**Solution**: Focus on forward-looking performance. Start tracking now and build a real performance record.

### Market Coverage

Not all days have active markets. Markets typically available:
- Weekdays: Usually available
- Weekends: Sometimes limited
- Holidays: May be limited

### Data Sources

Free forecast sources have limitations:
- API rate limits
- Occasional downtime
- Forecast accuracy varies

## Improving Performance

### 1. Add More Forecast Sources

Get an OpenWeatherMap API key (free tier):
```python
# In live_trader.py main()
decision = trader.make_trading_decision(openweathermap_key="YOUR_KEY")
```

### 2. Tune Confidence Thresholds

Modify `get_consensus_forecast()` in `live_trader.py` to adjust how confidence is calculated.

### 3. Time-of-Day Analysis

Track which time of day gives best forecasts:
- Morning (9 AM)
- Afternoon (2 PM)
- Evening (8 PM)

### 4. Weather Pattern Recognition

Some weather patterns are more predictable:
- Clear days: Higher confidence
- Transitional weather: Lower confidence
- Storm systems: Medium confidence

## Troubleshooting

### "No markets available for today"

Market might not be open yet or doesn't exist for that day. Check Kalshi directly.

### "Error fetching [Source]"

API timeout or rate limit. The system will work with available sources.

### "Could not find matching market"

Forecast temperature doesn't match any available bucket. This is rare but can happen with unusual temperatures.

## API Endpoints Used

### Kalshi API
- Base: `https://api.elections.kalshi.com/trade-api/v2`
- Public (no auth required)
- Endpoints:
  - `/markets` - Get market data
  - `/series/{ticker}` - Get series info

### Weather APIs
- Open-Meteo: `https://api.open-meteo.com/v1/forecast`
- NWS: `https://api.weather.gov/points/{lat},{lon}`
- OpenWeatherMap: `https://api.openweathermap.org/data/2.5/forecast`

## Championship Tips

1. **Consistency matters**: Trade every day when markets are available
2. **Document everything**: Keep notes on market conditions
3. **Learn patterns**: Some forecast sources better for certain weather
4. **Risk management**: Start with small positions while building track record
5. **Timing**: 9 AM your time seems optimal based on your experience

## Future Improvements

Potential enhancements:
1. **Machine learning**: Train on historical data
2. **Ensemble methods**: More sophisticated forecast combination
3. **Market microstructure**: Analyze order book dynamics
4. **Weather pattern classification**: Different strategies for different conditions
5. **Automated execution**: Direct API trading (requires Kalshi API auth)

## Questions?

Review the test scripts to understand how each component works:
- `test_data_access.py` - Verify data sources
- `test_historical_forecast.py` - Understand forecast data
- `test_market_details.py` - Explore Kalshi markets

## License

For educational use only. Trading involves risk.

Good luck in the championship! 🎯
