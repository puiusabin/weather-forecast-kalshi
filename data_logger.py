"""
Comprehensive data logging system
Logs everything that might be useful for strategy improvement
"""
import json
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
import requests


class ComprehensiveLogger:
    """Log all possible data points for analysis"""

    BASE_URL = "https://api.elections.kalshi.com/trade-api/v2"
    # Central Park coordinates (where NWS measures)
    NYC_LAT = 40.7831
    NYC_LON = -73.9712

    @staticmethod
    def get_weather_context() -> Dict[str, Any]:
        """Get current weather conditions and recent trend"""
        try:
            # Get last 3 days to see trend
            url = "https://archive-api.open-meteo.com/v1/archive"
            end_date = datetime.now()
            start_date = end_date - timedelta(days=3)

            params = {
                'latitude': ComprehensiveLogger.NYC_LAT,
                'longitude': ComprehensiveLogger.NYC_LON,
                'start_date': start_date.strftime('%Y-%m-%d'),
                'end_date': end_date.strftime('%Y-%m-%d'),
                'daily': 'temperature_2m_max,temperature_2m_min,precipitation_sum,windspeed_10m_max',
                'temperature_unit': 'fahrenheit',
                'timezone': 'America/New_York'
            }

            response = requests.get(url, params=params, timeout=10)
            if response.status_code == 200:
                data = response.json()
                daily = data['daily']

                temps = daily['temperature_2m_max']
                recent_temps = [t for t in temps if t is not None]

                if len(recent_temps) >= 2:
                    trend = "warming" if recent_temps[-1] > recent_temps[-2] else "cooling"
                    trend_magnitude = abs(recent_temps[-1] - recent_temps[-2])
                else:
                    trend = "stable"
                    trend_magnitude = 0

                return {
                    'recent_temps': recent_temps,
                    'trend': trend,
                    'trend_magnitude': trend_magnitude,
                    'recent_precip': daily.get('precipitation_sum', []),
                    'recent_windspeed': daily.get('windspeed_10m_max', []),
                    'yesterday_high': recent_temps[-1] if recent_temps else None
                }
        except Exception as e:
            print(f"Error getting weather context: {e}")

        return {}

    @staticmethod
    def analyze_all_markets(markets: List[Dict], forecast_temp: float) -> Dict[str, Any]:
        """Analyze all available markets, not just the one we trade"""
        import re

        market_analysis = {
            'total_markets': len(markets),
            'market_ranges': [],
            'selected_market': None,
            'adjacent_markets': [],
            'distance_to_adjacent': {},
            'market_spread': 0
        }

        if not markets:
            return market_analysis

        # Parse all market ranges
        for market in markets:
            subtitle = market['subtitle']

            # Parse temperature range
            range_match = re.search(r'(\d+)°\s+to\s+(\d+)°', subtitle)
            above_match = re.search(r'(\d+)°\s+or\s+above', subtitle)
            below_match = re.search(r'(\d+)°\s+or\s+below', subtitle)

            if range_match:
                low, high = float(range_match.group(1)), float(range_match.group(2))
                mid = (low + high) / 2
            elif above_match:
                low = float(above_match.group(1))
                mid = low + 5  # Estimate
            elif below_match:
                high = float(below_match.group(1))
                mid = high - 5  # Estimate
            else:
                continue

            market_analysis['market_ranges'].append({
                'subtitle': subtitle,
                'ticker': market['ticker'],
                'range': subtitle,
                'midpoint': mid,
                'distance_from_forecast': abs(mid - forecast_temp)
            })

        # Sort by distance from forecast
        market_analysis['market_ranges'].sort(key=lambda x: x['distance_from_forecast'])

        if market_analysis['market_ranges']:
            # Selected market (closest)
            market_analysis['selected_market'] = market_analysis['market_ranges'][0]

            # Adjacent markets
            if len(market_analysis['market_ranges']) > 1:
                market_analysis['adjacent_markets'] = market_analysis['market_ranges'][1:3]

                # Distance to adjacent
                for adj in market_analysis['adjacent_markets']:
                    market_analysis['distance_to_adjacent'][adj['subtitle']] = \
                        adj['distance_from_forecast']

            # Market spread (range of available markets)
            temps = [m['midpoint'] for m in market_analysis['market_ranges']]
            market_analysis['market_spread'] = max(temps) - min(temps)

        return market_analysis

    @staticmethod
    def calculate_confidence_breakdown(forecasts: Dict[str, float], consensus: float) -> Dict[str, Any]:
        """Detailed breakdown of why confidence is what it is"""
        breakdown = {
            'num_sources': len(forecasts),
            'source_agreement': {},
            'max_deviation': 0,
            'min_deviation': float('inf'),
            'sources_within_1_degree': 0,
            'sources_within_2_degrees': 0,
            'outliers': []
        }

        if not forecasts:
            return breakdown

        for source, temp in forecasts.items():
            deviation = abs(temp - consensus)
            breakdown['source_agreement'][source] = {
                'temp': temp,
                'deviation_from_consensus': deviation,
                'agrees': deviation < 1.0
            }

            breakdown['max_deviation'] = max(breakdown['max_deviation'], deviation)
            breakdown['min_deviation'] = min(breakdown['min_deviation'], deviation)

            if deviation <= 1.0:
                breakdown['sources_within_1_degree'] += 1
            if deviation <= 2.0:
                breakdown['sources_within_2_degrees'] += 1
            if deviation > 3.0:
                breakdown['outliers'].append(source)

        # Calculate agreement percentage
        breakdown['agreement_rate'] = breakdown['sources_within_1_degree'] / len(forecasts)

        return breakdown

    @staticmethod
    def get_historical_performance(trades_file: str = "data/trades.json") -> Dict[str, Any]:
        """Get running performance metrics"""
        try:
            with open(trades_file, 'r') as f:
                trades = json.load(f)
        except FileNotFoundError:
            trades = []

        performance = {
            'total_trades': len(trades),
            'recent_trades': 0,
            'recent_wins': 0,
            'recent_losses': 0,
            'consecutive_streak': 0,
            'avg_recent_confidence': 0
        }

        if not trades:
            return performance

        # Look at last 5 trades
        recent = trades[-5:] if len(trades) >= 5 else trades
        performance['recent_trades'] = len(recent)

        # Calculate recent confidence
        confidences = [t.get('confidence', 0) for t in recent]
        performance['avg_recent_confidence'] = sum(confidences) / len(confidences) if confidences else 0

        return performance

    @staticmethod
    def create_comprehensive_log_entry(
        date: str,
        forecasts: Dict[str, float],
        consensus: float,
        confidence: float,
        market_ticker: str,
        market_subtitle: str,
        markets: List[Dict]
    ) -> Dict[str, Any]:
        """Create ultra-detailed log entry with ALL useful data"""

        now = datetime.now()

        log_entry = {
            # Basic info
            'date': date,
            'timestamp': now.isoformat(),
            'day_of_week': now.strftime('%A'),
            'is_weekend': now.weekday() >= 5,

            # Forecast data
            'forecast_temp': consensus,
            'individual_forecasts': forecasts,
            'num_sources': len(forecasts),
            'sources_used': list(forecasts.keys()),

            # Decision
            'market_ticker': market_ticker,
            'market_subtitle': market_subtitle,
            'confidence': confidence,

            # Confidence breakdown
            'confidence_breakdown': ComprehensiveLogger.calculate_confidence_breakdown(
                forecasts, consensus
            ),

            # Market analysis
            'market_analysis': ComprehensiveLogger.analyze_all_markets(
                markets, consensus
            ),

            # Weather context
            'weather_context': ComprehensiveLogger.get_weather_context(),

            # Historical context
            'historical_performance': ComprehensiveLogger.get_historical_performance(),

            # Timing context
            'forecast_time': now.strftime('%H:%M:%S'),
            'hours_until_market_close': None,  # Could calculate from market data

            # Metadata for analysis
            'log_version': '2.0',  # Track logging schema version
            'notes': []  # For manual annotations
        }

        return log_entry


def test_logger():
    """Test the comprehensive logger"""
    print("Testing Comprehensive Logger\n")

    # Mock data
    forecasts = {
        'MSN': 60.0,
        'NWS': 58.0,
        'OpenMeteo': 59.5
    }

    markets = [
        {'ticker': 'TEST-B58.5', 'subtitle': '58° to 59°'},
        {'ticker': 'TEST-B59.5', 'subtitle': '59° to 60°'},
        {'ticker': 'TEST-B60.5', 'subtitle': '60° to 61°'},
    ]

    log_entry = ComprehensiveLogger.create_comprehensive_log_entry(
        date='2025-11-05',
        forecasts=forecasts,
        consensus=59.2,
        confidence=0.85,
        market_ticker='TEST-B59.5',
        market_subtitle='59° to 60°',
        markets=markets
    )

    print("Sample log entry:")
    print(json.dumps(log_entry, indent=2))

    print("\n✓ Logger working correctly")


if __name__ == "__main__":
    test_logger()
