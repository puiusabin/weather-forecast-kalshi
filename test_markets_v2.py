"""
Try different approaches to get market data
"""
import requests
import json

base_url = "https://api.elections.kalshi.com/trade-api/v2"

# Try getting markets with event_ticker filter
print("=== Approach 1: Get markets by event_ticker ===")
response = requests.get(f"{base_url}/markets", params={
    'event_ticker': 'KXHIGHNY-25NOV03',
    'limit': 20
})
print(f"Status: {response.status_code}")
if response.status_code == 200:
    data = response.json()
    markets = data.get('markets', [])
    print(f"Found {len(markets)} markets\n")

    for market in markets[:5]:
        print(f"Ticker: {market['ticker']}")
        print(f"  Subtitle: {market['subtitle']}")
        print(f"  Status: {market.get('status')}")
        print(f"  Result: {market.get('result')}")
        print()
else:
    print(f"Error: {response.text}\n")

# Try getting markets for the series with status filter
print("=== Approach 2: Get settled markets for series ===")
response = requests.get(f"{base_url}/markets", params={
    'series_ticker': 'KXHIGHNY',
    'status': 'settled',
    'limit': 10
})
print(f"Status: {response.status_code}")
if response.status_code == 200:
    data = response.json()
    markets = data.get('markets', [])
    print(f"Found {len(markets)} settled markets\n")

    # Group by event
    by_event = {}
    for market in markets:
        event = market.get('event_ticker')
        if event not in by_event:
            by_event[event] = []
        by_event[event].append(market)

    for event, event_markets in sorted(by_event.items())[:3]:
        print(f"\nEvent: {event}")
        winning = [m for m in event_markets if m.get('result') == 'yes']
        if winning:
            w = winning[0]
            print(f"  Winner: {w['subtitle']}")
            print(f"  Ticker: {w['ticker']}")
            print(f"  Close time: {w['close_time']}")
else:
    print(f"Error: {response.text}")
