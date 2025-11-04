"""
Test getting historical price data from Kalshi
"""
import requests
import json

base_url = "https://api.elections.kalshi.com/trade-api/v2"

# Get a settled market
ticker = "KXHIGHNY-25NOV03-B59.5"  # The winner

print(f"=== Getting price history for {ticker} ===\n")

# Try the trades endpoint
print("Approach 1: Trades endpoint")
response = requests.get(f"{base_url}/markets/{ticker}/trades", params={'limit': 10})
print(f"Status: {response.status_code}")
if response.status_code == 200:
    data = response.json()
    trades = data.get('trades', [])
    print(f"Found {len(trades)} trades")
    if trades:
        print("\nSample trades:")
        for trade in trades[:3]:
            print(f"  Time: {trade.get('created_time')}")
            print(f"  Price: {trade.get('yes_price')} cents")
            print(f"  Count: {trade.get('count')}")
            print()
else:
    print(f"Error: {response.text}\n")

# Try the candlesticks/history endpoint
print("\nApproach 2: History/Candlesticks")
response = requests.get(f"{base_url}/markets/{ticker}/history", params={
    'limit': 100,
    'min_ts': 1730505600  # Roughly early Nov
})
print(f"Status: {response.status_code}")
if response.status_code == 200:
    data = response.json()
    print(f"Keys: {data.keys()}")
    history = data.get('history', [])
    print(f"History points: {len(history)}")
    if history:
        print("\nSample prices:")
        for point in history[:5]:
            print(f"  {point}")
else:
    print(f"Error: {response.text[:200]}\n")

# Get orderbook snapshot
print("\nApproach 3: Current orderbook (for structure)")
response = requests.get(f"{base_url}/markets/{ticker}/orderbook")
print(f"Status: {response.status_code}")
if response.status_code == 200:
    data = response.json()
    print(f"Keys: {data.keys()}")
    if 'orderbook' in data:
        ob = data['orderbook']
        print(f"Orderbook keys: {ob.keys()}")
else:
    print(f"Error: {response.text[:200]}")
