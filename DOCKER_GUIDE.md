# Docker Setup Guide

## Quick Start

### 1. Build and Start Container

```bash
docker-compose up -d --build
```

This will:
- Build the Docker image
- Start the container in detached mode
- Begin automated daily trading at 9 AM (your timezone)

### 2. View Logs

```bash
# View cron logs (container logs)
docker-compose logs -f

# View trading logs
docker exec weather-trader cat /app/logs/trade_$(date +%Y-%m-%d).log
```

### 3. Check Collected Data

```bash
# View trades.json
docker exec weather-trader cat /app/data/trades.json

# Or access from host (data is persisted)
cat data/trades.json
```

### 4. Stop Container

```bash
docker-compose down
```

## Manual Testing

### Test Single Run

Before starting the automated system, test manually:

```bash
# Build container
docker-compose build

# Run once manually
docker-compose run --rm weather-trader python automated_runner.py
```

### Interactive Shell

```bash
docker exec -it weather-trader /bin/bash

# Inside container:
python live_trader.py
python track_performance.py
```

## Configuration

### Optional: Add OpenWeatherMap API Key

1. Create `.env` file:
```bash
cp .env.example .env
```

2. Edit `.env` and add your API key:
```
OPENWEATHERMAP_API_KEY=your_actual_key_here
```

3. Restart container:
```bash
docker-compose down
docker-compose up -d
```

### Change Trading Time

Edit `docker-compose.yml`:

```yaml
environment:
  - TRADING_TIME=09:00  # Change to your preferred time
```

Or edit `crontab` directly:

```cron
# Change from "0 9 * * *" to your preferred schedule
0 12 * * * cd /app && python automated_runner.py >> /var/log/cron.log 2>&1
```

Rebuild after changes:
```bash
docker-compose down
docker-compose up -d --build
```

## Data Collection Schedule

The container runs two automated tasks:

1. **9:00 AM** - Make trading decision
   - Fetch forecasts
   - Calculate consensus
   - Select market
   - Log decision

2. **10:00 AM** - Update performance metrics
   - Check previous day's results
   - Calculate win rate
   - Update statistics

## Monitoring

### Check if Container is Running

```bash
docker ps | grep weather-trader
```

### View Recent Logs

```bash
# Last 50 lines
docker-compose logs --tail=50

# Follow logs in real-time
docker-compose logs -f
```

### Check Cron Status

```bash
docker exec weather-trader ps aux | grep cron
```

## Data Persistence

Data is persisted in two directories:

- `./data/` - Trades data (trades.json)
- `./logs/` - Daily log files

These directories are mounted as volumes, so data persists even if container is stopped/removed.

## Troubleshooting

### Container Won't Start

```bash
# Check logs for errors
docker-compose logs

# Rebuild from scratch
docker-compose down
docker-compose build --no-cache
docker-compose up -d
```

### Cron Not Running

```bash
# Check cron service
docker exec weather-trader service cron status

# Manually test the script
docker exec weather-trader python /app/automated_runner.py
```

### Time Zone Issues

Verify timezone:
```bash
docker exec weather-trader date
```

Should show your local time (UTC+3). If not, check `TZ` environment variable in docker-compose.yml.

### No Data Being Collected

```bash
# Check if trades.json exists
docker exec weather-trader ls -la /app/data/

# Check for errors in logs
docker exec weather-trader cat /var/log/cron.log

# Run manually to see errors
docker exec weather-trader python /app/automated_runner.py
```

## One Week Collection Plan

### Day 0 (Today)

```bash
# Initial setup
docker-compose up -d --build

# Verify it's running
docker-compose logs

# Check first run (if after 9 AM, run manually)
docker exec weather-trader python automated_runner.py
```

### Days 1-6

Let it run automatically. Check daily:

```bash
# Morning check (after 9 AM)
docker-compose logs --tail=20

# View collected data
cat data/trades.json | jq .
```

### Day 7

```bash
# Stop container
docker-compose down

# Analyze collected data
python track_performance.py

# Review all logs
ls -l logs/
```

## Analysis After 7 Days

After collecting 7 days of data:

1. **Review trades.json**:
```bash
cat data/trades.json | jq '.[] | {date, forecast_temp, market_subtitle, confidence}'
```

2. **Check settled results**:
```bash
python track_performance.py
```

3. **Analyze patterns**:
```python
python analyze_week.py  # (create this based on findings)
```

4. **Adjust strategy**:
- Which forecast source was most accurate?
- Does confidence correlate with success?
- Are there better trading times?
- Should we adjust consensus algorithm?

## Next Steps After Data Collection

1. **Strategy refinement**: Based on 7-day data, tune parameters
2. **Add ML**: Train model on collected data
3. **Optimize timing**: Test different trading times
4. **Expand sources**: Add more forecast providers
5. **Risk management**: Adjust position sizing based on confidence

## Resource Usage

The container is lightweight:
- **CPU**: < 1% (only spikes during runs)
- **Memory**: ~50 MB
- **Disk**: < 100 MB
- **Network**: Minimal (only during forecast fetches)

Safe to run 24/7 on any system.

## Security Notes

- No authentication credentials stored (all APIs are public)
- No automated trading (decision logging only)
- Safe to run on public VPS
- Data is local only (no external reporting)

## Questions?

Check the main README.md for system details and trading strategy.
