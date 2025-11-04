"""
Automated runner for Docker container
Runs daily and collects trading data
"""
import os
import json
from datetime import datetime
from live_trader import LiveTrader


def ensure_data_dir():
    """Ensure data directory exists"""
    os.makedirs('/app/data', exist_ok=True)
    os.makedirs('/app/logs', exist_ok=True)


def get_trades_file():
    """Get trades file path"""
    return '/app/data/trades.json'


def get_log_file():
    """Get daily log file path"""
    date_str = datetime.now().strftime('%Y-%m-%d')
    return f'/app/logs/trade_{date_str}.log'


def log_message(message: str, also_print: bool = True):
    """Log message to file and optionally print"""
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    log_line = f"[{timestamp}] {message}\n"

    if also_print:
        print(log_line.strip())

    with open(get_log_file(), 'a') as f:
        f.write(log_line)


def run_daily_trade():
    """Run daily trading logic"""
    ensure_data_dir()

    log_message("="*60)
    log_message("Starting automated trading run")
    log_message("="*60)

    # Get API key from environment if available
    api_key = os.environ.get('OPENWEATHERMAP_API_KEY')
    weatherapi_key = os.environ.get('WEATHERAPI_KEY')

    # Import the enhanced trader for better source tracking
    from live_trader_enhanced import EnhancedLiveTrader
    trader = EnhancedLiveTrader()

    try:
        # Get all individual forecasts
        forecasts = trader.get_today_forecast(
            openweathermap_key=api_key,
            weatherapi_key=weatherapi_key
        )

        if forecasts:
            log_message("Individual forecasts:")
            for source, temp in forecasts.items():
                log_message(f"  {source}: {temp:.1f}°F")

        # Make trading decision
        decision = trader.make_trading_decision(
            openweathermap_key=api_key,
            weatherapi_key=weatherapi_key
        )

        if decision:
            # Save to persistent storage
            trades_file = get_trades_file()

            try:
                with open(trades_file, 'r') as f:
                    trades = json.load(f)
            except FileNotFoundError:
                trades = []

            # Use comprehensive logger for maximum data capture
            from data_logger import ComprehensiveLogger

            markets = trader.get_todays_markets()

            trade_data = ComprehensiveLogger.create_comprehensive_log_entry(
                date=decision.date,
                forecasts=forecasts,
                consensus=decision.forecast_temp,
                confidence=decision.confidence,
                market_ticker=decision.market_ticker,
                market_subtitle=decision.market_subtitle,
                markets=markets
            )

            trades.append(trade_data)

            with open(trades_file, 'w') as f:
                json.dump(trades, f, indent=2)

            log_message(f"✓ Trade logged successfully")
            log_message(f"  Market: {decision.market_subtitle}")
            log_message(f"  Ticker: {decision.market_ticker}")
            log_message(f"  Consensus: {decision.forecast_temp:.1f}°F")
            log_message(f"  Confidence: {decision.confidence:.1%}")
            log_message(f"  Sources: {', '.join(forecasts.keys())}")

            # Generate summary stats
            log_message("")
            log_message(f"Total trades recorded: {len(trades)}")

        else:
            log_message("⚠ Could not make trading decision")

    except Exception as e:
        log_message(f"✗ Error during trading run: {e}")
        import traceback
        log_message(traceback.format_exc())

    log_message("="*60)
    log_message("Automated run completed")
    log_message("="*60)


def analyze_collected_data():
    """Analyze data collected so far"""
    trades_file = get_trades_file()

    try:
        with open(trades_file, 'r') as f:
            trades = json.load(f)
    except FileNotFoundError:
        log_message("No trades data found yet")
        return

    log_message("")
    log_message("="*60)
    log_message("DATA COLLECTION SUMMARY")
    log_message("="*60)
    log_message(f"Days of data collected: {len(trades)}")

    if trades:
        first_date = trades[0]['date']
        last_date = trades[-1]['date']
        log_message(f"Date range: {first_date} to {last_date}")

        avg_confidence = sum(t['confidence'] for t in trades) / len(trades)
        log_message(f"Average confidence: {avg_confidence:.1%}")

        # Forecast distribution
        forecasts = [t['forecast_temp'] for t in trades]
        avg_forecast = sum(forecasts) / len(forecasts)
        log_message(f"Average forecast: {avg_forecast:.1f}°F")
        log_message(f"Forecast range: {min(forecasts):.1f}°F - {max(forecasts):.1f}°F")

    log_message("="*60)


if __name__ == "__main__":
    run_daily_trade()
    analyze_collected_data()
