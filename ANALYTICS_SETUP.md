# Analytics Setup with ClickHouse

## Overview

Your powerful server can now collect **massive amounts of data** with continuous monitoring:

- ✅ Temperature checks every 5 minutes during buffer period
- ✅ NWS + OpenMeteo observations logged
- ✅ ClickHouse database for fast analytics
- ✅ Grafana dashboards for visualization
- ✅ All data ready for strategy optimization

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                   Weather Trading System                     │
├─────────────────────────────────────────────────────────────┤
│                                                               │
│  ┌────────────────┐         ┌────────────────┐             │
│  │  Morning Check │────────>│  Get Forecast  │             │
│  │    (9 AM)      │         │  Max Time: 2PM │             │
│  └────────────────┘         └────────────────┘             │
│                                      │                       │
│                                      v                       │
│  ┌─────────────────────────────────────────────────┐       │
│  │      Buffer Period Monitoring (2 PM - 3 PM)     │       │
│  │  ┌──────────────────────────────────────────┐   │       │
│  │  │  Every 5 minutes:                        │   │       │
│  │  │  - Check NWS observation                 │   │       │
│  │  │  - Check OpenMeteo                       │   │       │
│  │  │  - Log to ClickHouse                     │   │       │
│  │  │  - Detect temperature decline            │   │       │
│  │  └──────────────────────────────────────────┘   │       │
│  └─────────────────────────────────────────────────┘       │
│                         │                                    │
│                         v                                    │
│  ┌──────────────────────────────────────┐                  │
│  │  Max Detected: 58°F at 2:15 PM       │                  │
│  │  Confidence: 90%                      │                  │
│  │  Bet: 57-58°F bucket                  │                  │
│  └──────────────────────────────────────┘                  │
│                         │                                    │
│                         v                                    │
│  ┌──────────────────────────────────────┐                  │
│  │  Push to ClickHouse:                  │                  │
│  │  - 12 observations (every 5 min)      │                  │
│  │  - Session metadata                   │                  │
│  │  - Bet decision                       │                  │
│  └──────────────────────────────────────┘                  │
└─────────────────────────────────────────────────────────────┘
                           │
                           v
┌─────────────────────────────────────────────────────────────┐
│                  ClickHouse Analytics DB                     │
├─────────────────────────────────────────────────────────────┤
│  📊 Tables:                                                  │
│  - temperature_observations (all 5-min checks)              │
│  - monitoring_sessions (daily session data)                 │
│  - daily_results (trading outcomes)                         │
│  - source_accuracy (compare NWS vs OpenMeteo)              │
│  - market_analysis (which buckets win)                      │
│                                                              │
│  🔍 Views:                                                   │
│  - win_rate_by_strategy                                     │
│  - source_rankings (which source is best?)                  │
│  - max_temp_hour_distribution                               │
│  - confidence_accuracy (does high confidence = high win?)   │
└─────────────────────────────────────────────────────────────┘
                           │
                           v
┌─────────────────────────────────────────────────────────────┐
│                    Grafana Dashboards                        │
├─────────────────────────────────────────────────────────────┤
│  📈 Real-time visualization:                                │
│  - Win rate over time                                        │
│  - Temperature prediction accuracy                           │
│  - Best performing sources                                   │
│  - Optimal betting times                                     │
└─────────────────────────────────────────────────────────────┘
```

## Setup Instructions

### Option 1: Full Analytics Stack (Recommended)

Includes: Weather Trader + ClickHouse + Grafana

```bash
cd ~/weather-forecast-kalshi

# Stop current setup
sudo docker-compose down

# Start analytics stack
sudo docker-compose -f docker-compose-analytics.yml up -d --build

# Verify all services running
sudo docker-compose -f docker-compose-analytics.yml ps
```

You should see:
```
weather-trader          Running
weather-analytics-db    Running
weather-grafana         Running
```

### Option 2: Basic Setup (Just Monitoring)

Without ClickHouse, data saved as JSON files:

```bash
# Use existing docker-compose.yml
sudo docker-compose up -d --build

# Monitoring data saved to ./data/monitoring/
# Can import to ClickHouse later
```

## Using the System

### 1. Continuous Monitoring

The system automatically:
- Checks forecast at 9 AM
- Starts monitoring at predicted max time
- Checks NWS + OpenMeteo every 5 minutes
- Detects when temp starts declining
- Places bet with high confidence

**Manual test:**
```bash
python smart_observed_strategy.py
```

Output example:
```
STARTING CONTINUOUS TEMPERATURE MONITORING
Predicted max: 63.0°F at 14:00
Buffer period: 14:00 to 15:00
Check interval: 300s (5 minutes)

--- Check #1 ---
[2025-11-06 14:00:05] NWS: 57.2°F (observed)
[2025-11-06 14:00:05] OpenMeteo: 57.5°F

--- Check #2 ---
[2025-11-06 14:05:12] NWS: 58.1°F (observed)
[2025-11-06 14:05:12] OpenMeteo: 58.2°F

--- Check #3 ---
[2025-11-06 14:10:18] NWS: 58.3°F (observed)
[2025-11-06 14:10:18] OpenMeteo: 58.1°F

--- Check #4 ---
[2025-11-06 14:15:25] NWS: 58.0°F (observed)
[2025-11-06 14:15:25] OpenMeteo: 57.8°F

✓ DECLINING TREND DETECTED
  Recent temps: 58.3°F → 58.1°F → 58.0°F
  Detected max: 58.3°F at 2025-11-06 14:10:18
  Confidence: 90.0%

MONITORING SESSION COMPLETE
Total observations: 8
Detected max: 58.3°F
Recommended bet: 58° to 59°
Confidence: 90.0%

💾 Session saved: /app/data/monitoring/monitoring_2025-11-06.json
   Ready for analytics import (ClickHouse/etc)
```

### 2. View Analytics (ClickHouse)

Connect to ClickHouse:
```bash
# CLI access
sudo docker exec -it weather-analytics-db clickhouse-client

# Inside ClickHouse:
USE weather_analytics;

# Check recent sessions
SELECT * FROM monitoring_sessions ORDER BY date DESC LIMIT 5;

# Win rate by strategy
SELECT * FROM win_rate_by_strategy;

# Source accuracy rankings
SELECT * FROM source_rankings;

# When does max temp usually occur?
SELECT * FROM max_temp_hour_distribution;
```

### 3. View Dashboards (Grafana)

Access Grafana: http://your-server:3000

**Default credentials:**
- Username: `admin`
- Password: `admin`

**Pre-built dashboards:**
- Trading Performance
- Source Accuracy
- Temperature Patterns
- Confidence Analysis

### 4. Import Historical Data

If you ran monitoring before setting up ClickHouse:

```bash
python clickhouse_logger.py

# Import specific session
python -c "from clickhouse_logger import import_json_session_to_clickhouse; \
           import_json_session_to_clickhouse('./data/monitoring/monitoring_2025-11-06.json')"
```

## Data Collection Volumes

With your powerful server, you can collect massive data:

### Per Day:
- **Monitoring period:** 1 hour (buffer period)
- **Check interval:** 5 minutes
- **Observations per day:** ~12 checks × 2 sources = 24 observations
- **Storage:** ~5 KB per day (JSON), ~2 KB (ClickHouse compressed)

### Per Month:
- **Total observations:** ~720 observations
- **Storage:** ~60 KB (ClickHouse)
- **Query speed:** <10ms for any analysis

### Per Year:
- **Total observations:** ~8,760 observations
- **Storage:** ~700 KB (ClickHouse compressed)
- **Patterns detected:** Seasonal trends, day-of-week effects, optimal timing

## Analytics Queries

### Find best performing hours
```sql
SELECT
    actual_max_hour,
    COUNT(*) as days,
    AVG(confidence) as avg_confidence,
    AVG(CASE WHEN bet_won = 1 THEN 1 ELSE 0 END) as win_rate
FROM monitoring_sessions
WHERE bet_placed = 1
GROUP BY actual_max_hour
ORDER BY win_rate DESC;
```

### Compare NWS vs OpenMeteo accuracy
```sql
SELECT
    source,
    AVG(error) as avg_error,
    STDDEV(error) as error_stddev,
    COUNT(*) as observations
FROM source_accuracy
GROUP BY source
ORDER BY avg_error;
```

### Identify best days to trade
```sql
SELECT
    w.day_of_week,
    COUNT(*) as trades,
    AVG(d.trade_won) as win_rate,
    AVG(d.confidence) as avg_confidence
FROM daily_results d
JOIN weather_context w ON d.date = w.date
WHERE d.trade_placed = 1
GROUP BY w.day_of_week
ORDER BY win_rate DESC;
```

### Find confidence sweet spot
```sql
SELECT
    ROUND(confidence, 1) as conf_bucket,
    COUNT(*) as trades,
    AVG(trade_won) as win_rate
FROM daily_results
WHERE trade_placed = 1
GROUP BY conf_bucket
ORDER BY conf_bucket;
```

## Performance Considerations

### API Rate Limits

**NWS:**
- No official limit
- Be respectful: 1 request per 5 min = safe
- 12 requests/hour = well under any limit

**OpenMeteo:**
- 10,000 requests/day (free tier)
- 12 requests/hour × 24 hours = 288/day
- Usage: ~3% of daily limit

### Server Resources

ClickHouse requirements:
- RAM: 2 GB minimum
- Disk: 10 GB for years of data
- CPU: Minimal (analytics queries cached)

### Network Usage

Per monitoring session:
- 12 NWS requests × ~5 KB = 60 KB
- 12 OpenMeteo requests × ~10 KB = 120 KB
- Total: ~180 KB per day

## Maintenance

### Backup Data

```bash
# Backup ClickHouse data
sudo docker exec weather-analytics-db clickhouse-client \
  --query="SELECT * FROM monitoring_sessions FORMAT CSVWithNames" \
  > backup_sessions.csv

# Backup JSON monitoring files
tar -czf monitoring_backup.tar.gz ./data/monitoring/
```

### Clear Old Data

```sql
-- Delete data older than 1 year
DELETE FROM temperature_observations
WHERE date < today() - INTERVAL 365 DAY;

-- Optimize table
OPTIMIZE TABLE temperature_observations FINAL;
```

## Troubleshooting

### ClickHouse not starting
```bash
# Check logs
sudo docker logs weather-analytics-db

# Check disk space
df -h
```

### Monitoring not saving data
```bash
# Check directory permissions
ls -la ./data/monitoring/

# Create if missing
mkdir -p ./data/monitoring/
chmod 777 ./data/monitoring/
```

### Grafana can't connect to ClickHouse
```bash
# Test ClickHouse HTTP
curl http://localhost:8123/ping

# Check network
sudo docker-compose -f docker-compose-analytics.yml ps
```

## Next Steps

1. **Deploy analytics stack:**
   ```bash
   sudo docker-compose -f docker-compose-analytics.yml up -d --build
   ```

2. **Run first monitoring session:**
   ```bash
   sudo docker exec weather-trader python /app/smart_observed_strategy.py
   ```

3. **Check data in ClickHouse:**
   ```bash
   sudo docker exec -it weather-analytics-db clickhouse-client
   ```

4. **Set up Grafana dashboards:**
   - Go to http://your-server:3000
   - Add ClickHouse datasource
   - Import pre-built dashboards

5. **Collect 7 days of data:**
   - System runs automatically
   - Data accumulates in ClickHouse
   - Analyze patterns weekly

## Benefits of This Setup

✅ **Comprehensive data:** Every 5-minute observation logged
✅ **Fast analytics:** ClickHouse queries in milliseconds
✅ **Pattern discovery:** Find optimal timing automatically
✅ **Source comparison:** Which forecast is actually best?
✅ **Strategy validation:** Prove what works with data
✅ **Scalable:** Can handle years of data easily
✅ **Visual:** Grafana dashboards for insights

---

*Analytics system designed for your powerful server*
*Capable of processing millions of observations*
*Optimized for trading strategy development*
