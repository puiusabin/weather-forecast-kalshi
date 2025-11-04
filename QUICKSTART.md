# Quick Start Guide

## What You Have

A complete weather trading system for Kalshi markets with:

✓ Multiple forecast sources (Open-Meteo, NWS, optional: MSN, OpenWeatherMap)
✓ Automated daily trading decisions
✓ Docker setup for 7-day data collection
✓ Performance tracking and analysis tools
✓ Strategy optimization based on collected data

## Immediate Next Steps

### Option 1: Manual Trading (Start Today)

```bash
# Install dependencies
pip install -r requirements.txt

# Make today's decision
python live_trader_enhanced.py

# Check trades.json for your recommendation
```

Then manually trade on Kalshi at 9 AM your time.

### Option 2: Automated Data Collection (1 Week)

```bash
# Start Docker container
docker-compose up -d --build

# Monitor
docker-compose logs -f

# Let it run for 7 days
```

After 7 days:
```bash
# Stop collection
docker-compose down

# Analyze overall performance
python analyze_week.py

# Compare forecast sources (NEW!)
python analyze_sources.py

# Optimize strategy
python strategy_optimizer.py
```

## Championship Strategy

### Week 1: Data Collection Phase

1. **Start Docker container** (today)
2. **Let it run for 7 days** collecting forecasts and results
3. **No manual trading yet** - just observe and collect data

### Week 2: Trading Phase

1. **Analyze collected data**:
   ```bash
   python analyze_week.py
   python strategy_optimizer.py
   ```

2. **Apply optimizations** based on findings

3. **Start manual trading**:
   - Every day at 9 AM your time
   - Run: `python live_trader_enhanced.py`
   - Execute recommended trade on Kalshi
   - Target entry: 40-50¢

### Ongoing

1. **Daily routine** (9 AM your time):
   ```bash
   python live_trader_enhanced.py
   ```

2. **Weekly review**:
   ```bash
   python track_performance.py
   ```

3. **Adjust as needed** based on win rate

## Key Files

### For Daily Use
- `live_trader_enhanced.py` - Main trading system (use this)
- `trades.json` - Your trade log (now includes individual source data!)

### For Analysis
- `track_performance.py` - Check your win rate
- `analyze_week.py` - Detailed weekly analysis
- `analyze_sources.py` - Compare forecast source accuracy (NEW!)
- `strategy_optimizer.py` - Get improvement suggestions

### For Docker
- `docker-compose.yml` - Container configuration
- `DOCKER_GUIDE.md` - Detailed Docker instructions

### Documentation
- `README.md` - Full system documentation
- This file - Quick start

## Important Notes

### Forecast Sources

Based on your research:
- ✓ **MSN Weather**: Best accuracy (enabled by default with higher weight)
- ✗ **Google Weather**: Avoid (not included)
- ✓ **NWS**: Official US source (included)
- ✓ **Open-Meteo**: Good baseline (included)

### Trading Timing

- **Best time**: 9 AM your time (UTC+3)
- **Why**: Markets typically 40-50¢ (good value)
- **Settlement**: ~4 AM EST next day

### Win Rate Targets

- Random guessing: ~16.7% (1 in 6 markets)
- Target: >30% for positive returns
- Excellent: >40% win rate

### Expected Returns

At 45¢ entry price:
- Win rate 30%: Break even to slight loss
- Win rate 35%: +11% ROI
- Win rate 40%: +22% ROI
- Win rate 50%: +56% ROI

## Troubleshooting

### "No forecasts available"
Check internet connection. System needs at least one source to work.

### "No markets available"
Market might not exist for that day. Check Kalshi directly.

### Docker not running
```bash
docker-compose ps
docker-compose logs
```

### Low win rate
After 7+ days of data, run `strategy_optimizer.py` for suggestions.

## Pro Tips

1. **Be consistent**: Trade every day when markets available
2. **Track everything**: System auto-logs to trades.json
3. **High confidence only**: Consider only trading when confidence >70%
4. **Start small**: Test strategy with small positions first
5. **Review weekly**: Run analysis every 7 days

## Getting Help

Check detailed guides:
- System overview: `README.md`
- Docker setup: `DOCKER_GUIDE.md`
- Test scripts: `test_*.py` files

## Championship Checklist

Week 1 (Data Collection):
- [ ] Start Docker container
- [ ] Verify daily runs (check logs)
- [ ] Monitor data collection

Week 2 (Analysis):
- [ ] Stop container after 7 days
- [ ] Run analyze_week.py
- [ ] Run strategy_optimizer.py
- [ ] Apply optimizations

Week 3+ (Trading):
- [ ] Daily 9 AM: Run live_trader_enhanced.py
- [ ] Execute trades on Kalshi
- [ ] Weekly: Check track_performance.py
- [ ] Adjust strategy as needed

## Contact / Questions

Review test scripts to understand components:
- `test_data_access.py` - Data source verification
- `test_market_details.py` - Kalshi market structure
- `data_fetchers.py` - Core data fetching logic

Good luck in the championship! 🎯

---

*Last updated: Nov 4, 2025*
