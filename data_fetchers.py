"""
Data fetching modules for weather forecasts and Kalshi markets
"""
import requests
import re
from datetime import datetime, timedelta
from typing import Optional, Dict, List, Tuple
from dataclasses import dataclass


@dataclass
class ActualTemp:
    """Actual maximum temperature for a day"""
    date: str
    temp_f: float
    source: str = "NWS"


@dataclass
class ForecastTemp:
    """Forecasted maximum temperature"""
    forecast_date: str  # When the forecast was made
    target_date: str    # What day the forecast is for
    temp_f: float
    source: str


@dataclass
class KalshiMarket:
    """Kalshi market information"""
    ticker: str
    event_ticker: str
    subtitle: str  # e.g., "59° to 60°"
    date: str
    result: Optional[str]  # 'yes', 'no', or None if not settled
    close_time: str
    temp_range: Tuple[float, float]  # (low, high) or (threshold, float('inf'))


class NWSDataFetcher:
    """Fetch actual temperature data from NWS Climate Reports"""

    BASE_URL = "https://forecast.weather.gov/product.php"

    @staticmethod
    def get_actual_temp(date: datetime) -> Optional[ActualTemp]:
        """
        Get actual max temp for a specific date from NWS CLI.
        Note: This only works for recent dates (last few days).
        """
        params = {
            'site': 'OKX',
            'product': 'CLI',
            'issuedby': 'NYC'
        }

        response = requests.get(NWSDataFetcher.BASE_URL, params=params)
        if response.status_code != 200:
            return None

        text = response.text

        # Look for the date in the report
        date_str = date.strftime('%B %-d %Y').upper()

        # Find MAXIMUM temp in TEMPERATURE section
        temp_match = re.search(r'MAXIMUM\s+(\d+)', text)
        if temp_match:
            max_temp = float(temp_match.group(1))
            return ActualTemp(
                date=date.strftime('%Y-%m-%d'),
                temp_f=max_temp,
                source='NWS'
            )

        return None

    @staticmethod
    def parse_cli_report(text: str, target_date: datetime) -> Optional[float]:
        """
        Parse a CLI report to extract max temp.
        This is more robust than get_actual_temp for historical reports.
        """
        # The report format has MAXIMUM followed by temp and time
        temp_match = re.search(r'MAXIMUM\s+(\d+)', text)
        if temp_match:
            return float(temp_match.group(1))
        return None


class OpenMeteoFetcher:
    """Fetch historical forecast data from Open-Meteo"""

    # NYC coordinates
    LAT = 40.7128
    LON = -74.0060

    @staticmethod
    def get_historical_forecast(
        forecast_date: datetime,
        target_date: datetime
    ) -> Optional[ForecastTemp]:
        """
        Get the forecast that was made on forecast_date for target_date.

        Args:
            forecast_date: When the forecast was issued
            target_date: What day the forecast is for
        """
        url = "https://historical-forecast-api.open-meteo.com/v1/forecast"

        params = {
            'latitude': OpenMeteoFetcher.LAT,
            'longitude': OpenMeteoFetcher.LON,
            'start_date': target_date.strftime('%Y-%m-%d'),
            'end_date': target_date.strftime('%Y-%m-%d'),
            'daily': 'temperature_2m_max',
            'temperature_unit': 'fahrenheit',
            'timezone': 'America/New_York'
        }

        try:
            response = requests.get(url, params=params, timeout=10)
            if response.status_code == 200:
                data = response.json()
                if 'daily' in data and 'temperature_2m_max' in data['daily']:
                    temps = data['daily']['temperature_2m_max']
                    if temps and temps[0] is not None:
                        return ForecastTemp(
                            forecast_date=forecast_date.strftime('%Y-%m-%d'),
                            target_date=target_date.strftime('%Y-%m-%d'),
                            temp_f=temps[0],
                            source='OpenMeteo'
                        )
        except Exception as e:
            print(f"Error fetching forecast: {e}")

        return None

    @staticmethod
    def get_actual_temp(date: datetime) -> Optional[float]:
        """
        Get actual temperature from Open-Meteo archive.
        This is a backup to NWS data.
        """
        url = "https://archive-api.open-meteo.com/v1/archive"

        params = {
            'latitude': OpenMeteoFetcher.LAT,
            'longitude': OpenMeteoFetcher.LON,
            'start_date': date.strftime('%Y-%m-%d'),
            'end_date': date.strftime('%Y-%m-%d'),
            'daily': 'temperature_2m_max',
            'temperature_unit': 'fahrenheit',
            'timezone': 'America/New_York'
        }

        try:
            response = requests.get(url, params=params, timeout=10)
            if response.status_code == 200:
                data = response.json()
                if 'daily' in data and 'temperature_2m_max' in data['daily']:
                    temps = data['daily']['temperature_2m_max']
                    if temps and temps[0] is not None:
                        return temps[0]
        except Exception as e:
            print(f"Error fetching actual temp: {e}")

        return None


class KalshiFetcher:
    """Fetch market data from Kalshi API"""

    BASE_URL = "https://api.elections.kalshi.com/trade-api/v2"

    @staticmethod
    def parse_market_range(subtitle: str) -> Tuple[float, float]:
        """
        Parse market subtitle to get temperature range.

        Examples:
            "59° to 60°" -> (59, 60)
            "65° or above" -> (65, inf)
            "56° or below" -> (-inf, 56)
        """
        # Range format: "59° to 60°"
        range_match = re.search(r'(\d+)°\s+to\s+(\d+)°', subtitle)
        if range_match:
            return (float(range_match.group(1)), float(range_match.group(2)))

        # Above format: "65° or above"
        above_match = re.search(r'(\d+)°\s+or\s+above', subtitle)
        if above_match:
            return (float(above_match.group(1)), float('inf'))

        # Below format: "56° or below"
        below_match = re.search(r'(\d+)°\s+or\s+below', subtitle)
        if below_match:
            return (float('-inf'), float(below_match.group(1)))

        return (0, 0)

    @staticmethod
    def get_markets_for_date(date: datetime) -> List[KalshiMarket]:
        """Get all markets for a specific date"""
        # Format: KXHIGHNY-25NOV03
        event_ticker = f"KXHIGHNY-{date.strftime('%y%b%d').upper()}"

        response = requests.get(
            f"{KalshiFetcher.BASE_URL}/markets",
            params={'event_ticker': event_ticker, 'limit': 20}
        )

        if response.status_code != 200:
            return []

        markets_data = response.json().get('markets', [])
        markets = []

        for m in markets_data:
            temp_range = KalshiFetcher.parse_market_range(m['subtitle'])
            markets.append(KalshiMarket(
                ticker=m['ticker'],
                event_ticker=m['event_ticker'],
                subtitle=m['subtitle'],
                date=date.strftime('%Y-%m-%d'),
                result=m.get('result'),
                close_time=m.get('close_time', ''),
                temp_range=temp_range
            ))

        return markets

    @staticmethod
    def find_winning_market(
        markets: List[KalshiMarket],
        actual_temp: float
    ) -> Optional[KalshiMarket]:
        """Find which market won based on actual temperature"""
        for market in markets:
            low, high = market.temp_range
            if low <= actual_temp <= high:
                return market
        return None

    @staticmethod
    def find_market_for_forecast(
        markets: List[KalshiMarket],
        forecast_temp: float
    ) -> Optional[KalshiMarket]:
        """Find which market we should bet on based on forecast"""
        for market in markets:
            low, high = market.temp_range
            if low <= forecast_temp <= high:
                return market
        return None


if __name__ == "__main__":
    # Quick test
    print("Testing data fetchers...\n")

    # Test OpenMeteo
    today = datetime.now()
    past_date = today - timedelta(days=3)

    print(f"=== Testing forecast for {past_date.date()} ===")
    forecast = OpenMeteoFetcher.get_historical_forecast(past_date, past_date)
    if forecast:
        print(f"Forecast: {forecast.temp_f}°F")

    actual = OpenMeteoFetcher.get_actual_temp(past_date)
    if actual:
        print(f"Actual: {actual}°F")

    # Test Kalshi
    print(f"\n=== Testing Kalshi markets for {past_date.date()} ===")
    markets = KalshiFetcher.get_markets_for_date(past_date)
    print(f"Found {len(markets)} markets")

    if markets and actual:
        predicted = KalshiFetcher.find_market_for_forecast(markets, forecast.temp_f)
        winner = KalshiFetcher.find_winning_market(markets, actual)

        print(f"\nForecast {forecast.temp_f}°F -> Would bet on: {predicted.subtitle if predicted else 'None'}")
        print(f"Actual {actual}°F -> Winner was: {winner.subtitle if winner else 'None'}")
        print(f"Match: {predicted.subtitle == winner.subtitle if (predicted and winner) else False}")
