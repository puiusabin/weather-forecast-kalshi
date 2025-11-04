# Weekly Improvement Cycle

## Overview

You have until end of year. This means ~8 weeks to iterate and improve. Each week you'll collect data, analyze, optimize, and trade better.

## What's Being Logged Now

### Comprehensive Data (v2.0 Logging)

Every trade now logs:

1. **Basic Info**
   - Date, timestamp, day of week
   - Is weekend/weekday

2. **Forecast Data**
   - Consensus temperature
   - Individual forecasts from each source
   - Number of sources available
   - Which sources were used

3. **Market Data**
   - All available markets (not just the one traded)
   - Distance to adjacent markets
   - Market spread
   - Selected market and why

4. **Confidence Breakdown**
   - Source agreement details
   - Max/min deviations
   - Number of sources within 1°F/2°F
   - Outlier sources

5. **Weather Context**
   - Recent temperature trend
   - Warming/cooling pattern
   - Yesterday's high
   - Recent precipitation
   - Wind conditions

6. **Historical Context**
   - Total trades so far
   - Recent performance
   - Consecutive streak
   - Average recent confidence

7. **Timing Info**
   - What time forecast was made
   - Hours until market closes

## The 8-Week Plan

### Week 1: Baseline Collection (Current Week)
```bash
# Start Docker
sudo docker-compose up -d --build

# Let it run 7 days
# Don't trade yet - just collect data
```

**Goal**: Get baseline data with comprehensive logging

### Week 2: First Analysis
```bash
# Stop collection
sudo docker-compose down

# Generate full report
python weekly_report.py > week2_report.txt

# Read the action items
cat week2_report.txt
```

**Goal**:
- Identify which forecast source is best
- Find optimal confidence threshold
- Discover patterns

**Actions**:
- Adjust source weights based on accuracy
- Set minimum confidence threshold
- Start manual trading with insights

### Week 3-4: Refinement
```bash
# Apply optimizations from week 2
# Edit live_trader_enhanced.py with new weights

# Rebuild and run
sudo docker-compose up -d --build

# Trade manually based on recommendations
python live_trader_enhanced.py  # Every morning
```

**Goal**: Test optimizations from week 2 analysis

**Track**:
- Did win rate improve?
- Is confidence better calibrated?
- Any new patterns?

### Week 5-6: Pattern Exploitation
```bash
# Weekly report
python weekly_report.py

# Focus on pattern analysis
python analyze_patterns.py
```

**Goal**: Exploit discovered patterns
- Best days to trade
- Weather conditions that predict accuracy
- Source combinations that work

**Example Findings**:
- "MSN + NWS together = 85% accuracy"
- "Warming trends = lower forecast error"
- "Thursday forecasts = most reliable"

### Week 7-8: Final Optimization
```bash
# Full analysis
python weekly_report.py

# Compare to week 1 baseline
# Calculate improvement
```

**Goal**: Fine-tune everything for championship

**Metrics to Track**:
- Week 1 win rate vs Week 8 win rate
- Confidence calibration improvement
- Forecast error reduction
- Profitability increase

## Weekly Workflow

### Sunday Evening: Analysis Day

```bash
# 1. Stop container
sudo docker-compose down

# 2. Pull latest code
cd ~/weather-forecast-kalshi
git pull

# 3. Generate comprehensive report
python weekly_report.py > reports/week_$(date +%U).txt

# 4. Review and take notes
less reports/week_$(date +%U).txt

# 5. Apply optimizations
# Edit configuration/code based on findings

# 6. Rebuild and restart
sudo docker-compose up -d --build
```

### Daily (Monday-Friday): Trading Days

```bash
# 9:00 AM (your time)
# Docker runs automatically, or manually:
python live_trader_enhanced.py

# Review recommendation
cat data/trades.json | tail -20

# Execute trade on Kalshi if confidence >70%
```

### Quick Health Check (Any day)

```bash
# Check recent logs
sudo docker-compose logs --tail=50

# Check data quality
python -c "import json; trades = json.load(open('data/trades.json')); print(f'{len(trades)} trades, last: {trades[-1][\"date\"]}')"

# Quick stats
python track_performance.py
```

## Analysis Tools Reference

### 1. weekly_report.py
**Master report - Run this every Sunday**

Shows:
- Executive summary
- Overall performance
- Source comparison
- Pattern analysis
- Strategy optimization
- Action items for next week

Usage:
```bash
python weekly_report.py > reports/week_current.txt
```

### 2. analyze_sources.py
**Which forecast source is best?**

Shows:
- Accuracy rankings
- Average error by source
- Source bias (over/under forecasting)
- Recommended weights

Usage:
```bash
python analyze_sources.py
```

### 3. analyze_patterns.py
**Find hidden patterns**

Shows:
- Day of week patterns
- Weather trend effects
- Source combination performance
- Market proximity analysis
- Optimal confidence thresholds

Usage:
```bash
python analyze_patterns.py
```

### 4. strategy_optimizer.py
**Get specific parameter recommendations**

Shows:
- Optimal confidence threshold
- Bias corrections needed
- Weight adjustments

Usage:
```bash
python strategy_optimizer.py
```

### 5. track_performance.py
**Quick win rate check**

Shows:
- Current win rate
- Recent performance
- Profitability estimate

Usage:
```bash
python track_performance.py
```

## Key Metrics to Track Weekly

### Performance Metrics
- Win rate (target: >35%)
- Win rate trend (improving?)
- Consecutive wins/losses
- Profitability (ROI)

### Forecast Metrics
- Average error (target: <1.5°F)
- Error by source
- Confidence calibration
- Source availability

### Pattern Metrics
- Best day of week
- Best weather conditions
- Best source combinations
- Optimal confidence threshold

## Expected Improvement Trajectory

### Week 1: Baseline
- Win rate: ~25-30% (better than random)
- Learning: Which sources work
- Confidence: Not well calibrated

### Week 3-4: Early Optimization
- Win rate: ~30-35%
- Learning: Patterns emerging
- Confidence: Better calibrated
- Source weights: Optimized

### Week 6-7: Pattern Exploitation
- Win rate: ~35-40%
- Learning: Strong patterns identified
- Confidence: Well calibrated
- Trading: Only high-confidence days

### Week 8: Championship Ready
- Win rate: 40%+ (target)
- Learning: All patterns internalized
- Confidence: Excellent calibration
- Trading: Consistent profits

## Data-Driven Decisions

### What data will tell you:

1. **"MSN is actually best"**
   → Increase MSN weight to 3.0x

2. **"Warming trends = higher accuracy"**
   → Increase confidence on warming days

3. **"Thursdays are most predictable"**
   → Trade more aggressively on Thursdays

4. **"MSN + NWS combo is gold"**
   → Require both sources for high confidence

5. **"Confidence >80% = 60% win rate"**
   → Only trade when confidence >80%

6. **"Market proximity matters"**
   → Avoid trades near bucket edges

## Championship Strategy

### Phase 1: Data Collection (Week 1-2)
- Collect without trading
- Focus on data quality
- Ensure all sources working

### Phase 2: Learning (Week 3-4)
- Start trading conservatively
- Small positions
- Test hypotheses

### Phase 3: Optimization (Week 5-6)
- Apply learned patterns
- Increase position sizes
- Focus on high-confidence only

### Phase 4: Execution (Week 7-8)
- Trade optimally
- Track against classmates
- Aim for top 20%

## Red Flags to Watch

1. **Win rate declining**
   → Review recent changes
   → Check source availability
   → Verify confidence calibration

2. **Confidence not correlating with wins**
   → Recalibrate confidence algorithm
   → Check source weights

3. **One source consistently wrong**
   → Reduce weight or remove
   → Investigate why

4. **Patterns not holding**
   → Market dynamics changed
   → Need fresh analysis

5. **Low source availability**
   → MSN scraping failing
   → Add backup sources

## Success Metrics

### By End of Year (Week 8)

**Minimum (Pass)**:
- Win rate: >30%
- ROI: Break-even
- Ranking: Top 50% of class

**Target (Good)**:
- Win rate: 35-40%
- ROI: 15-25%
- Ranking: Top 30% of class

**Excellent (A+)**:
- Win rate: >40%
- ROI: >25%
- Ranking: Top 20% of class

## Notes Template

Keep weekly notes:

```markdown
# Week X Notes

## This Week's Data
- Trades: X
- Win rate: X%
- Best source: X
- New patterns: X

## Changes Made
1. Adjusted MSN weight to X
2. Set confidence threshold to X%
3. Added bias correction of +X°F

## Results
- Win rate changed by: +X%
- Confidence improved by: X%
- New insights: X

## Next Week Plan
1. Test X hypothesis
2. Optimize X parameter
3. Watch for X pattern
```

## Remember

1. **Data > Intuition**: Let data guide decisions
2. **Iterate Weekly**: Each week makes you better
3. **Document Everything**: Track what works
4. **Small Changes**: Don't change too much at once
5. **Confidence Matters**: Only trade high confidence

You have 8 weeks to get this right. Use the data. Every week you'll be smarter and more profitable.

Good luck! 🎯

---

*Guide created: Nov 4, 2025*
*Duration: 8 weeks until end of year*
*Target: Top 20% of class*
