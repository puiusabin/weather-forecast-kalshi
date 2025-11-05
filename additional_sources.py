"""
Additional weather forecast sources
Including web scraping for sources without public APIs
"""
import requests
from bs4 import BeautifulSoup
from typing import Optional
from datetime import datetime
import re
import json


class AdditionalWeatherSources:
    """Forecast sources that require scraping or alternative access"""

    @staticmethod
    def get_foreca() -> Optional[float]:
        """
        Get forecast from Foreca for NYC Central Park
        Foreca is known for good European and US forecasts
        """
        try:
            # Foreca URL for Central Park, Manhattan (10024 zip code for Upper West Side near Central Park)
            # This is closer to where NWS measures than generic "New York"
            url = "https://www.foreca.com/United-States/New-York/Manhattan"

            headers = {
                'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
            }

            response = requests.get(url, headers=headers, timeout=15)

            if response.status_code == 200:
                soup = BeautifulSoup(response.text, 'html.parser')

                # Foreca typically shows high temp prominently
                # Look for temperature elements
                temp_selectors = [
                    'span.temp_high',
                    'span[class*="high"]',
                    'div[class*="temp"][class*="max"]',
                    'span.value'
                ]

                for selector in temp_selectors:
                    elements = soup.select(selector)
                    if elements:
                        for elem in elements[:3]:  # Check first few
                            text = elem.get_text()
                            # Extract number
                            temp_match = re.search(r'(\d+)', text)
                            if temp_match:
                                temp = float(temp_match.group(1))
                                # Foreca might be in Celsius, check if reasonable
                                if temp < 50:  # Likely Celsius
                                    temp = (temp * 9/5) + 32
                                if 30 <= temp <= 110:  # Sanity check for Fahrenheit
                                    return temp

        except Exception as e:
            print(f"Error fetching Foreca: {e}")

        return None

    @staticmethod
    def get_weather_channel() -> Optional[float]:
        """
        Get forecast from The Weather Channel for NYC Central Park
        weather.com is owned by IBM and often very accurate
        """
        try:
            # Weather Channel URL for Central Park NYC (where NWS gets data)
            # Coordinates: 40.7831, -73.9712
            url = "https://weather.com/weather/today/l/40.78,-73.97"

            headers = {
                'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36',
                'Accept-Language': 'en-US,en;q=0.9'
            }

            response = requests.get(url, headers=headers, timeout=15)

            if response.status_code == 200:
                soup = BeautifulSoup(response.text, 'html.parser')

                # Look for high temperature
                # Weather.com uses various class names
                temp_selectors = [
                    'span[data-testid="TemperatureValue"]',
                    'div[class*="TodayDetailsCard"] span[class*="temp"]',
                    'span.CurrentConditions--tempValue--',
                    'div[data-testid="wxData"] span'
                ]

                for selector in temp_selectors:
                    elements = soup.select(selector)
                    if elements:
                        # Usually the high is shown prominently
                        for elem in elements[:5]:
                            text = elem.get_text()
                            # Extract just the number
                            temp_match = re.search(r'(\d+)', text)
                            if temp_match:
                                temp = float(temp_match.group(1))
                                # Sanity check
                                if 30 <= temp <= 110:
                                    return temp

                # Alternative: look in JSON-LD structured data
                scripts = soup.find_all('script', type='application/ld+json')
                for script in scripts:
                    try:
                        data = json.loads(script.string)
                        if isinstance(data, dict) and 'temperature' in str(data):
                            # Try to extract temperature
                            pass
                    except:
                        continue

        except Exception as e:
            print(f"Error fetching Weather Channel: {e}")

        return None

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
                        temp = float(temp_str)
                        # AccuWeather US site should be in Fahrenheit, but check
                        if temp < 50:  # Likely Celsius
                            temp = (temp * 9/5) + 32
                        if 30 <= temp <= 110:  # Sanity check
                            return temp

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
    print("Testing Additional Weather Sources (Based on User Research)\n")
    print("="*60)

    sources = {
        'Foreca': AdditionalWeatherSources.get_foreca,
        'Weather Channel': AdditionalWeatherSources.get_weather_channel,
        'MSN Weather': AdditionalWeatherSources.get_msn_weather,
        'Weather.com': AdditionalWeatherSources.get_weathercom,
        'AccuWeather': AdditionalWeatherSources.get_accuweather,
    }

    print("\n🌟 Priority sources (per user research for NYC):")
    print("   1. Foreca")
    print("   2. Weather Channel")
    print("   3. MSN Weather\n")

    for name, func in sources.items():
        print(f"Testing {name}...")
        try:
            temp = func()
            if temp:
                print(f"  ✓ {temp}°F")
            else:
                print(f"  ✗ No data")
        except Exception as e:
            print(f"  ✗ Error: {e}")

    print("\n" + "="*60)
    print("\nNote: Web scraping sources may be blocked or rate limited")
    print("Test each source and use ones that work consistently")


if __name__ == "__main__":
    test_all_sources()
