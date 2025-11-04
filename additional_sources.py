"""
Additional weather forecast sources
Including web scraping for sources without public APIs
"""
import requests
from bs4 import BeautifulSoup
from typing import Optional
from datetime import datetime


class AdditionalWeatherSources:
    """Forecast sources that require scraping or alternative access"""

    @staticmethod
    def get_msn_weather() -> Optional[float]:
        """
        Get forecast from MSN Weather for NYC
        MSN Weather aggregates data from multiple sources
        """
        try:
            # MSN Weather URL for New York City
            url = "https://www.msn.com/en-us/weather/forecast/in-New-York,NY"

            headers = {
                'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
            }

            response = requests.get(url, headers=headers, timeout=15)

            if response.status_code == 200:
                soup = BeautifulSoup(response.text, 'html.parser')

                # Look for temperature data
                # MSN uses various class names, try multiple selectors
                selectors = [
                    'div[data-testid="TemperatureValue"]',
                    'span.temperature',
                    'div.current-temp',
                    '[class*="temperature"]'
                ]

                for selector in selectors:
                    temp_elements = soup.select(selector)
                    if temp_elements:
                        # Extract number from text
                        temp_text = temp_elements[0].get_text()
                        # Remove non-digit characters except minus
                        temp_str = ''.join(c for c in temp_text if c.isdigit() or c == '-')
                        if temp_str:
                            return float(temp_str)

        except Exception as e:
            print(f"Error fetching MSN Weather: {e}")

        return None

    @staticmethod
    def get_weathercom() -> Optional[float]:
        """
        Get forecast from Weather.com for NYC
        Weather.com is often accurate for US locations
        """
        try:
            # Weather.com location code for NYC
            url = "https://weather.com/weather/today/l/40.71,-74.01"

            headers = {
                'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
            }

            response = requests.get(url, headers=headers, timeout=15)

            if response.status_code == 200:
                soup = BeautifulSoup(response.text, 'html.parser')

                # Look for high temperature
                temp_elements = soup.find_all('span', {'data-testid': 'TemperatureValue'})

                if temp_elements:
                    # First one is usually the high
                    temp_text = temp_elements[0].get_text()
                    temp_str = ''.join(c for c in temp_text if c.isdigit())
                    if temp_str:
                        return float(temp_str)

        except Exception as e:
            print(f"Error fetching Weather.com: {e}")

        return None

    @staticmethod
    def get_accuweather() -> Optional[float]:
        """
        Get forecast from AccuWeather for NYC
        Note: AccuWeather has rate limiting
        """
        try:
            # AccuWeather location key for NYC
            url = "https://www.accuweather.com/en/us/new-york-ny/10007/weather-forecast/349727"

            headers = {
                'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
            }

            response = requests.get(url, headers=headers, timeout=15)

            if response.status_code == 200:
                soup = BeautifulSoup(response.text, 'html.parser')

                # Look for temperature in forecast
                temp_element = soup.find('div', class_='temp')
                if temp_element:
                    temp_text = temp_element.get_text()
                    temp_str = ''.join(c for c in temp_text if c.isdigit())
                    if temp_str:
                        return float(temp_str)

        except Exception as e:
            print(f"Error fetching AccuWeather: {e}")

        return None

    @staticmethod
    def get_weatherapi_com(api_key: Optional[str] = None) -> Optional[float]:
        """
        Get forecast from WeatherAPI.com
        Free tier: 1 million calls/month
        Sign up at: https://www.weatherapi.com/
        """
        if not api_key:
            return None

        try:
            url = "http://api.weatherapi.com/v1/forecast.json"
            params = {
                'key': api_key,
                'q': '40.7128,-74.0060',  # NYC coords
                'days': 1
            }

            response = requests.get(url, params=params, timeout=10)

            if response.status_code == 200:
                data = response.json()
                # Get today's forecast
                forecast_day = data['forecast']['forecastday'][0]
                return forecast_day['day']['maxtemp_f']

        except Exception as e:
            print(f"Error fetching WeatherAPI.com: {e}")

        return None


def test_all_sources():
    """Test all additional sources"""
    print("Testing Additional Weather Sources\n")
    print("="*60)

    sources = {
        'MSN Weather': AdditionalWeatherSources.get_msn_weather,
        'Weather.com': AdditionalWeatherSources.get_weathercom,
        'AccuWeather': AdditionalWeatherSources.get_accuweather,
    }

    for name, func in sources.items():
        print(f"\nTesting {name}...")
        try:
            temp = func()
            if temp:
                print(f"✓ {name}: {temp}°F")
            else:
                print(f"✗ {name}: No data")
        except Exception as e:
            print(f"✗ {name}: Error - {e}")

    print("\n" + "="*60)
    print("\nNote: Web scraping sources may be blocked or rate limited")
    print("Use these as supplementary sources, not primary ones")


if __name__ == "__main__":
    test_all_sources()
