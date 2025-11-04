"""
Investigate Kalshi KXHIGHNY market structure
"""
import requests
import json
from datetime import datetime, timedelta

base_url = "https://api.elections.kalshi.com/trade-api/v2"

# Get series info
print("=== KXHIGHNY Series Info ===")
response = requests.get(f"{base_url}/series/KXHIGHNY")
if response.status_code == 200:
    series = response.json()['series']
    print(f"Title: {series.get('title')}")
    print(f"Category: {series.get('category')}")
    print(f"Frequency: {series.get('frequency')}")
    print()

# Get recent events
print("=== Recent Events ===")
response = requests.get(f"{base_url}/events", params={
    'series_ticker': 'KXHIGHNY',
    'status': 'settled',
    'limit': 5
})

if response.status_code == 200:
    events = response.json().get('events', [])
    for event in events[:3]:
        print(f"\nEvent: {event.get('event_ticker')}")
        print(f"  Title: {event.get('title')}")
        print(f"  Strike date: {event.get('strike_date')}")
        print(f"  Mutually exclusive: {event.get('mutually_exclusive')}")

        # Get markets for this event
        market_response = requests.get(f"{base_url}/events/{event.get('event_ticker')}/markets")
        if market_response.status_code == 200:
            markets = market_response.json().get('markets', [])
            print(f"  Number of markets: {len(markets)}")

            # Show first few markets
            for market in markets[:3]:
                print(f"    - {market.get('ticker')}: {market.get('subtitle')}")
                print(f"      Close time: {market.get('close_time')}")
                print(f"      Yes bid: {market.get('yes_bid')}, Ask: {market.get('yes_ask')}")
                print(f"      Result: {market.get('result')}")

# Try to get a specific recent market
date_str = (datetime.now() - timedelta(days=2)).strftime('%y%b%d').lower()
ticker = f"KXHIGHNY-{date_str}"
print(f"\n=== Specific Market: {ticker} ===")

response = requests.get(f"{base_url}/markets/{ticker}")
if response.status_code == 200:
    market = response.json().get('market')
    print(json.dumps(market, indent=2))
else:
    print(f"Error: {response.status_code}")
    print(response.text[:500])
