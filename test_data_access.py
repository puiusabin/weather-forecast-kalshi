"""
Test script to verify we can access all required data sources.
"""
import requests
from datetime import datetime, timedelta
import re

def test_nws_cli():
    """Test accessing NWS Climate Report for NYC"""
    print("\n=== Testing NWS CLI Access ===")
    url = "https://forecast.weather.gov/product.php?site=OKX&product=CLI&issuedby=NYC"
    response = requests.get(url)
    print(f"Status: {response.status_code}")

    if response.status_code == 200:
        # Parse max temp from today's report
        text = response.text
        # Look for MAXIMUM temp line in TEMPERATURE section
        temp_match = re.search(r'MAXIMUM\s+(\d+)', text)
        if temp_match:
            max_temp = temp_match.group(1)
            print(f"Found max temp: {max_temp}°F")
            return True
        else:
            print("Could not parse max temp")
            return False
    return False

def test_open_meteo():
    """Test Open-Meteo Historical Forecast API"""
    print("\n=== Testing Open-Meteo API ===")

    # NYC coordinates: 40.7128° N, 74.0060° W
    lat = 40.7128
    lon = -74.0060

    # Get forecast from 3 days ago
    date = (datetime.now() - timedelta(days=3)).strftime('%Y-%m-%d')

    url = "https://api.open-meteo.com/v1/forecast"
    params = {
        'latitude': lat,
        'longitude': lon,
        'daily': 'temperature_2m_max',
        'temperature_unit': 'fahrenheit',
        'timezone': 'America/New_York',
        'start_date': date,
        'end_date': date
    }

    response = requests.get(url, params=params)
    print(f"Status: {response.status_code}")

    if response.status_code == 200:
        data = response.json()
        print(f"Response keys: {data.keys()}")
        if 'daily' in data:
            print(f"Max temp forecast: {data['daily']['temperature_2m_max']}")
            return True
    return False

def test_kalshi_api():
    """Test Kalshi API access"""
    print("\n=== Testing Kalshi API ===")

    # Try to get event info for KXHIGHNY
    base_url = "https://api.elections.kalshi.com/trade-api/v2"

    # First, let's try to get series info
    response = requests.get(f"{base_url}/series/KXHIGHNY")
    print(f"Series endpoint status: {response.status_code}")

    if response.status_code == 200:
        data = response.json()
        print(f"Series data keys: {data.keys()}")
        return True

    # If that doesn't work, try events endpoint
    response = requests.get(f"{base_url}/events?series_ticker=KXHIGHNY")
    print(f"Events endpoint status: {response.status_code}")

    if response.status_code == 200:
        data = response.json()
        print(f"Events data: {data}")
        return True

    return False

if __name__ == "__main__":
    print("Testing data source access...\n")

    results = {
        'NWS CLI': test_nws_cli(),
        'Open-Meteo': test_open_meteo(),
        'Kalshi API': test_kalshi_api()
    }

    print("\n=== Results ===")
    for source, success in results.items():
        status = "✓" if success else "✗"
        print(f"{status} {source}")
