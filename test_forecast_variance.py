"""
Test if Open-Meteo historical forecasts vary by lead time
"""
import requests
from datetime import datetime, timedelta

# NYC coordinates
lat = 40.7128
lon = -74.0060

# Pick a date 10 days ago
target_date = datetime.now() - timedelta(days=10)

print(f"Target date: {target_date.date()}")
print("Testing if forecasts differ by lead time...\n")

# Get "forecasts" made 0, 1, 2, 3 days before
forecasts = {}

for days_before in range(4):
    forecast_date = target_date - timedelta(days=days_before)

    url = "https://historical-forecast-api.open-meteo.com/v1/forecast"
    params = {
        'latitude': lat,
        'longitude': lon,
        'start_date': target_date.strftime('%Y-%m-%d'),
        'end_date': target_date.strftime('%Y-%m-%d'),
        'daily': 'temperature_2m_max',
        'temperature_unit': 'fahrenheit',
        'timezone': 'America/New_York'
    }

    response = requests.get(url, params=params, timeout=10)
    if response.status_code == 200:
        data = response.json()
        temp = data['daily']['temperature_2m_max'][0]
        forecasts[days_before] = temp
        print(f"{days_before} days before: {temp}°F")

# Check if they're all the same
if len(set(forecasts.values())) == 1:
    print("\n⚠️ WARNING: All forecasts are identical!")
    print("This suggests Open-Meteo is not providing true historical forecasts.")
else:
    print("\n✓ Forecasts vary by lead time")

# Get actual
url = "https://archive-api.open-meteo.com/v1/archive"
params = {
    'latitude': lat,
    'longitude': lon,
    'start_date': target_date.strftime('%Y-%m-%d'),
    'end_date': target_date.strftime('%Y-%m-%d'),
    'daily': 'temperature_2m_max',
    'temperature_unit': 'fahrenheit',
    'timezone': 'America/New_York'
}
response = requests.get(url, params=params, timeout=10)
if response.status_code == 200:
    data = response.json()
    actual = data['daily']['temperature_2m_max'][0]
    print(f"\nActual: {actual}°F")
