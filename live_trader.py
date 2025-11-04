"""
Live trading system for Kalshi weather markets
"""
import requests
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass
import json


@dataclass
class ForecastSource:
    """Different weather forecast providers"""
    name: str
    get_forecast_func: callable


@dataclass
class TradingDecision:
    """Decision for a single market"""
    date: str
    forecast_temp: float
    source: str
    market_ticker: str
    market_subtitle: str
    confidence: float  # 0-1


class WeatherForecasts:
    """Fetch forecasts from multiple sources"""

    NYC_LAT = 40.7128
    NYC_LON = -74.0060

    @staticmethod
    def get_openmeteo_forecast(target_date: datetime) -> Optional[float]:
        """Get forecast from Open-Meteo (free)"""
        url = "https://api.open-meteo.com/v1/forecast"
        params = {
            'latitude': WeatherForecasts.NYC_LAT,
            'longitude': WeatherForecasts.NYC_LON,
            'daily': 'temperature_2m_max',
            'temperature_unit': 'fahrenheit',
            'timezone': 'America/New_York',
            'forecast_days': 3
        }

        try:
            response = requests.get(url, params=params, timeout=10)
            if response.status_code == 200:
                data = response.json()
                # Find the right day
                dates = data['daily']['time']
                temps = data['daily']['temperature_2m_max']
                target_str = target_date.strftime('%Y-%m-%d')

                for i, date_str in enumerate(dates):
                    if date_str == target_str:
                        return temps[i]
        except Exception as e:
            print(f"Error fetching Open-Meteo: {e}")
        return None

    @staticmethod
    def get_nws_forecast(target_date: datetime) -> Optional[float]:
        """Get forecast from weather.gov"""
        # NWS API point forecast for NYC (Central Park)
        # Latitude: 40.7831, Longitude: -73.9712
        try:
            # First get the gridpoints
            lat, lon = 40.7831, -73.9712
            points_url = f"https://api.weather.gov/points/{lat},{lon}"
            headers = {'User-Agent': 'Weather Trading Bot'}

            response = requests.get(points_url, headers=headers, timeout=10)
            if response.status_code == 200:
                data = response.json()
                forecast_url = data['properties']['forecast']

                # Get the forecast
                forecast_response = requests.get(forecast_url, headers=headers, timeout=10)
                if forecast_response.status_code == 200:
                    forecast_data = forecast_response.json()
                    periods = forecast_data['properties']['periods']

                    # Find the period for our target date
                    target_str = target_date.strftime('%Y-%m-%d')
                    for period in periods:
                        period_date = period['startTime'][:10]
                        if period_date == target_str and period['isDaytime']:
                            return float(period['temperature'])
        except Exception as e:
            print(f"Error fetching NWS: {e}")
        return None

    @staticmethod
    def get_openweathermap_forecast(target_date: datetime, api_key: Optional[str] = None) -> Optional[float]:
        """
        Get forecast from OpenWeatherMap (requires API key)
        Free tier: 1000 calls/day
        Sign up at: https://openweathermap.org/api
        """
        if not api_key:
            return None

        url = "https://api.openweathermap.org/data/2.5/forecast"
        params = {
            'lat': WeatherForecasts.NYC_LAT,
            'lon': WeatherForecasts.NYC_LON,
            'appid': api_key,
            'units': 'imperial'
        }

        try:
            response = requests.get(url, params=params, timeout=10)
            if response.status_code == 200:
                data = response.json()
                target_str = target_date.strftime('%Y-%m-%d')

                # Find max temp for target date
                max_temp = None
                for item in data['list']:
                    dt_str = item['dt_txt'][:10]
                    if dt_str == target_str:
                        temp = item['main']['temp_max']
                        if max_temp is None or temp > max_temp:
                            max_temp = temp

                return max_temp
        except Exception as e:
            print(f"Error fetching OpenWeatherMap: {e}")
        return None


class LiveTrader:
    """Main trading system"""

    BASE_URL = "https://api.elections.kalshi.com/trade-api/v2"

    def __init__(self):
        self.trades_log = []

    def get_today_forecast(self, openweathermap_key: Optional[str] = None) -> Dict[str, float]:
        """Get forecasts from all available sources for today"""
        today = datetime.now()

        forecasts = {}

        # Open-Meteo (free)
        temp = WeatherForecasts.get_openmeteo_forecast(today)
        if temp:
            forecasts['OpenMeteo'] = temp

        # NWS (free)
        temp = WeatherForecasts.get_nws_forecast(today)
        if temp:
            forecasts['NWS'] = temp

        # OpenWeatherMap (requires API key)
        if openweathermap_key:
            temp = WeatherForecasts.get_openweathermap_forecast(today, openweathermap_key)
            if temp:
                forecasts['OpenWeatherMap'] = temp

        return forecasts

    def get_todays_markets(self) -> List[Dict]:
        """Get today's Kalshi markets"""
        today = datetime.now()
        event_ticker = f"KXHIGHNY-{today.strftime('%y%b%d').upper()}"

        response = requests.get(
            f"{self.BASE_URL}/markets",
            params={'event_ticker': event_ticker, 'limit': 20}
        )

        if response.status_code == 200:
            return response.json().get('markets', [])
        return []

    def find_best_market(self, markets: List[Dict], forecast_temp: float) -> Optional[Dict]:
        """Find which market to trade based on forecast"""
        import re

        for market in markets:
            subtitle = market['subtitle']

            # Parse range
            range_match = re.search(r'(\d+)°\s+to\s+(\d+)°', subtitle)
            if range_match:
                low, high = float(range_match.group(1)), float(range_match.group(2))
                if low <= forecast_temp <= high:
                    return market

            # Above
            above_match = re.search(r'(\d+)°\s+or\s+above', subtitle)
            if above_match:
                threshold = float(above_match.group(1))
                if forecast_temp >= threshold:
                    return market

            # Below
            below_match = re.search(r'(\d+)°\s+or\s+below', subtitle)
            if below_match:
                threshold = float(below_match.group(1))
                if forecast_temp <= threshold:
                    return market

        return None

    def get_consensus_forecast(self, forecasts: Dict[str, float]) -> Tuple[float, float]:
        """
        Get consensus forecast and confidence from multiple sources

        Returns: (consensus_temp, confidence)
        """
        if not forecasts:
            return None, 0.0

        temps = list(forecasts.values())
        consensus = sum(temps) / len(temps)

        # Calculate confidence based on agreement
        # Higher confidence if sources agree
        if len(temps) > 1:
            variance = sum((t - consensus) ** 2 for t in temps) / len(temps)
            std_dev = variance ** 0.5
            # Confidence inversely related to std dev
            # 0 std dev = 1.0 confidence, 3°F std dev = 0.5 confidence
            confidence = max(0.0, 1.0 - std_dev / 6.0)
        else:
            confidence = 0.7  # Single source = moderate confidence

        return consensus, confidence

    def make_trading_decision(self, openweathermap_key: Optional[str] = None) -> Optional[TradingDecision]:
        """Make trading decision for today"""
        # Get forecasts
        forecasts = self.get_today_forecast(openweathermap_key)

        if not forecasts:
            print("No forecasts available")
            return None

        print(f"\nForecasts for {datetime.now().date()}:")
        for source, temp in forecasts.items():
            print(f"  {source}: {temp:.1f}°F")

        # Get consensus
        consensus, confidence = self.get_consensus_forecast(forecasts)
        print(f"\nConsensus: {consensus:.1f}°F (confidence: {confidence:.1%})")

        # Get markets
        markets = self.get_todays_markets()

        if not markets:
            print("No markets available for today")
            return None

        print(f"\nAvailable markets: {len(markets)}")

        # Find best market
        best_market = self.find_best_market(markets, consensus)

        if not best_market:
            print("Could not find matching market")
            return None

        decision = TradingDecision(
            date=datetime.now().strftime('%Y-%m-%d'),
            forecast_temp=consensus,
            source="Consensus",
            market_ticker=best_market['ticker'],
            market_subtitle=best_market['subtitle'],
            confidence=confidence
        )

        print(f"\n{'='*60}")
        print(f"TRADING DECISION:")
        print(f"  Market: {best_market['subtitle']}")
        print(f"  Ticker: {best_market['ticker']}")
        print(f"  Confidence: {confidence:.1%}")
        print(f"{'='*60}\n")

        return decision

    def log_trade(self, decision: TradingDecision, filename: str = "trades.json"):
        """Log trade decision to file"""
        trade_data = {
            'date': decision.date,
            'forecast_temp': decision.forecast_temp,
            'source': decision.source,
            'market_ticker': decision.market_ticker,
            'market_subtitle': decision.market_subtitle,
            'confidence': decision.confidence,
            'timestamp': datetime.now().isoformat()
        }

        try:
            # Read existing trades
            try:
                with open(filename, 'r') as f:
                    trades = json.load(f)
            except FileNotFoundError:
                trades = []

            # Add new trade
            trades.append(trade_data)

            # Write back
            with open(filename, 'w') as f:
                json.dump(trades, f, indent=2)

            print(f"Trade logged to {filename}")
        except Exception as e:
            print(f"Error logging trade: {e}")


def main():
    """Run the live trading system"""
    print("="*60)
    print("LIVE WEATHER TRADING SYSTEM")
    print("="*60)

    trader = LiveTrader()

    # Make decision
    decision = trader.make_trading_decision()

    if decision:
        # Log the trade
        trader.log_trade(decision)

        print("\nNext steps:")
        print(f"1. Go to Kalshi and find market: {decision.market_ticker}")
        print(f"2. Buy 'Yes' on: {decision.market_subtitle}")
        print(f"3. The market closes tomorrow morning (~4 AM EST)")
        print(f"4. Settlement based on: https://forecast.weather.gov/product.php?site=OKX&product=CLI&issuedby=NYC")


if __name__ == "__main__":
    main()
