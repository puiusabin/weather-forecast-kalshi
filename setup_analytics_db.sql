-- ClickHouse Analytics Schema for Weather Trading
-- Run this to create tables for comprehensive data analysis

-- 1. Temperature Observations Table
-- Stores every single observation (5-minute intervals)
CREATE TABLE IF NOT EXISTS temperature_observations (
    timestamp DateTime,
    date Date,
    hour UInt8,
    minute UInt8,
    source String,  -- 'NWS', 'OpenMeteo', 'MSN', etc.
    temperature Float32,
    is_forecast UInt8,  -- 0 = observed, 1 = forecast
    session_id String  -- Links to monitoring_sessions
) ENGINE = MergeTree()
PARTITION BY toYYYYMM(date)
ORDER BY (date, timestamp, source);

-- 2. Monitoring Sessions Table
-- One row per day's monitoring session
CREATE TABLE IF NOT EXISTS monitoring_sessions (
    session_id String,
    date Date,
    start_time DateTime,
    end_time DateTime,
    predicted_max_hour UInt8,
    predicted_max_temp Float32,
    detected_max_temp Float32,
    detected_max_time DateTime,
    actual_max_temp Float32,  -- From settlement (filled next day)
    actual_max_hour UInt8,    -- When actual max occurred
    confidence Float32,
    bet_decision String,
    bet_placed UInt8,         -- 0 = no, 1 = yes
    bet_won UInt8,            -- 0 = no, 1 = yes, NULL = not settled yet
    observations_count UInt16,
    duration_minutes UInt16
) ENGINE = MergeTree()
PARTITION BY toYYYYMM(date)
ORDER BY (date, session_id);

-- 3. Daily Trading Results Table
-- High-level daily results
CREATE TABLE IF NOT EXISTS daily_results (
    date Date,
    strategy String,  -- 'CoolingTrend', 'ObservedData', 'ForecastBased'
    forecast_consensus Float32,
    forecast_confidence Float32,
    observed_max Float32,
    actual_max Float32,
    predicted_correct UInt8,  -- Did prediction match reality?
    trade_placed UInt8,
    trade_won UInt8,
    market_ticker String,
    market_subtitle String,
    settlement_time DateTime,
    error_magnitude Float32,  -- abs(predicted - actual)
    sources_used Array(String),
    num_sources UInt8
) ENGINE = MergeTree()
PARTITION BY toYYYYMM(date)
ORDER BY date;

-- 4. Source Accuracy Tracking
-- Track each source's accuracy over time
CREATE TABLE IF NOT EXISTS source_accuracy (
    date Date,
    source String,
    forecast_temp Float32,
    actual_temp Float32,
    error Float32,
    was_available UInt8,
    fetch_time DateTime
) ENGINE = MergeTree()
PARTITION BY toYYYYMM(date)
ORDER BY (source, date);

-- 5. Market Analysis Table
-- Track market characteristics and outcomes
CREATE TABLE IF NOT EXISTS market_analysis (
    date Date,
    market_ticker String,
    market_subtitle String,
    bucket_low Float32,
    bucket_high Float32,
    total_markets_available UInt8,
    adjacent_market_spread Float32,
    chosen_market_confidence Float32,
    actual_max_temp Float32,
    market_won UInt8
) ENGINE = MergeTree()
PARTITION BY toYYYYMM(date)
ORDER BY (date, market_ticker);

-- 6. Weather Context Table
-- Environmental factors that might affect accuracy
CREATE TABLE IF NOT EXISTS weather_context (
    date Date,
    day_of_week String,
    is_weekend UInt8,
    recent_temps Array(Float32),  -- Last 3 days
    temp_trend String,  -- 'warming', 'cooling', 'stable'
    trend_magnitude Float32,
    season String,  -- 'winter', 'spring', 'summer', 'fall'
    precipitation_chance Float32,
    cloud_cover Float32
) ENGINE = MergeTree()
PARTITION BY toYYYYMM(date)
ORDER BY date;

-- Analytics Views

-- Win rate by strategy
CREATE VIEW IF NOT EXISTS win_rate_by_strategy AS
SELECT
    strategy,
    COUNT(*) as total_trades,
    SUM(trade_won) as wins,
    AVG(trade_won) as win_rate,
    AVG(error_magnitude) as avg_error,
    AVG(forecast_confidence) as avg_confidence
FROM daily_results
WHERE trade_placed = 1
GROUP BY strategy
ORDER BY win_rate DESC;

-- Win rate by day of week
CREATE VIEW IF NOT EXISTS win_rate_by_dow AS
SELECT
    w.day_of_week,
    COUNT(*) as trades,
    SUM(d.trade_won) as wins,
    AVG(d.trade_won) as win_rate,
    AVG(d.error_magnitude) as avg_error
FROM daily_results d
JOIN weather_context w ON d.date = w.date
WHERE d.trade_placed = 1
GROUP BY w.day_of_week
ORDER BY
    CASE w.day_of_week
        WHEN 'Monday' THEN 1
        WHEN 'Tuesday' THEN 2
        WHEN 'Wednesday' THEN 3
        WHEN 'Thursday' THEN 4
        WHEN 'Friday' THEN 5
        WHEN 'Saturday' THEN 6
        WHEN 'Sunday' THEN 7
    END;

-- Source accuracy rankings
CREATE VIEW IF NOT EXISTS source_rankings AS
SELECT
    source,
    COUNT(*) as days_available,
    AVG(error) as avg_error,
    STDDEV(error) as error_stddev,
    AVG(was_available) as availability_rate
FROM source_accuracy
GROUP BY source
ORDER BY avg_error ASC;

-- Best performing hours for max temp
CREATE VIEW IF NOT EXISTS max_temp_hour_distribution AS
SELECT
    actual_max_hour,
    COUNT(*) as occurrences,
    AVG(ABS(predicted_max_hour - actual_max_hour)) as avg_timing_error,
    SUM(CASE WHEN predicted_max_hour = actual_max_hour THEN 1 ELSE 0 END) as correct_predictions
FROM monitoring_sessions
WHERE actual_max_temp IS NOT NULL
GROUP BY actual_max_hour
ORDER BY actual_max_hour;

-- Temperature change patterns
CREATE VIEW IF NOT EXISTS temp_change_patterns AS
SELECT
    date,
    detected_max_temp,
    actual_max_temp,
    ABS(detected_max_temp - actual_max_temp) as detection_error,
    CASE
        WHEN detected_max_temp > actual_max_temp THEN 'overestimated'
        WHEN detected_max_temp < actual_max_temp THEN 'underestimated'
        ELSE 'exact'
    END as error_direction
FROM monitoring_sessions
WHERE actual_max_temp IS NOT NULL
ORDER BY date DESC;

-- Confidence vs accuracy correlation
CREATE VIEW IF NOT EXISTS confidence_accuracy AS
SELECT
    ROUND(confidence, 1) as confidence_bucket,
    COUNT(*) as trades,
    AVG(trade_won) as win_rate,
    AVG(error_magnitude) as avg_error
FROM daily_results
WHERE trade_placed = 1
GROUP BY confidence_bucket
ORDER BY confidence_bucket DESC;
