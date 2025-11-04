"""
Test if Open-Meteo provides actual historical forecast data (archived predictions).
"""
import requests
from datetime import datetime, timedelta

# NYC coordinates
lat = 40.7128
lon = -74.0060

# Test: Get forecast that was made 5 days ago for 5 days ago
# If this is truly historical forecast data, it should match what was predicted then
# Not what we know now
past_date = (datetime.now() - timedelta(days=5)).strftime('%Y-%m-%d')

print(f"Testing historical forecast for date: {past_date}")
print("This should be the forecast that was made on that day, not current knowledge\n")

# Try the archive endpoint
url = "https://archive-api.open-meteo.com/v1/archive"
params = {
    'latitude': lat,
    'longitude': lon,
    'start_date': past_date,
    'end_date': past_date,
    'daily': 'temperature_2m_max',
    'temperature_unit': 'fahrenheit',
    'timezone': 'America/New_York'
}

print("=== Trying archive API (actual weather) ===")
response = requests.get(url, params=params)
print(f"Status: {response.status_code}")
if response.status_code == 200:
    data = response.json()
    print(f"Archive max temp: {data['daily']['temperature_2m_max']}")

# Try forecast archive
# This is the key - we need the forecast that was issued at a specific time
url = "https://previous-runs-api.open-meteo.com/v1/forecast"
params = {
    'latitude': lat,
    'longitude': lon,
    'start_date': past_date,
    'end_date': past_date,
    'daily': 'temperature_2m_max',
    'temperature_unit': 'fahrenheit',
    'timezone': 'America/New_York'
}

print("\n=== Trying previous-runs API (historical forecasts) ===")
response = requests.get(url, params=params)
print(f"Status: {response.status_code}")
if response.status_code == 200:
    data = response.json()
    print(f"Historical forecast max temp: {data['daily']['temperature_2m_max']}")
else:
    print(f"Error: {response.text}")

# Check if historical forecast API exists at all
url = "https://historical-forecast-api.open-meteo.com/v1/forecast"
print("\n=== Trying historical-forecast-api ===")
response = requests.get(url, params=params)
print(f"Status: {response.status_code}")
if response.status_code == 200:
    data = response.json()
    print(f"Data: {data}")
else:
    print(f"Response: {response.text[:200]}")
