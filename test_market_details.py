"""
Get detailed market information for a specific event
"""
import requests
import json

base_url = "https://api.elections.kalshi.com/trade-api/v2"

# Get a recent settled event
event_ticker = "KXHIGHNY-25NOV03"

print(f"=== Markets for {event_ticker} ===\n")
response = requests.get(f"{base_url}/events/{event_ticker}/markets")

if response.status_code == 200:
    markets = response.json().get('markets', [])
    print(f"Total markets: {len(markets)}\n")

    # Group by result
    settled = [m for m in markets if m.get('result') is not None]
    winning = [m for m in settled if m.get('result') == 'yes']

    print(f"Settled markets: {len(settled)}")
    print(f"Winning markets: {len(winning)}\n")

    if winning:
        print("=== Winning Market ===")
        winner = winning[0]
        print(f"Ticker: {winner['ticker']}")
        print(f"Subtitle: {winner['subtitle']}")
        print(f"Close time: {winner['close_time']}")
        print(f"Result: {winner['result']}")
        if 'yes_bid' in winner:
            print(f"Final Yes bid: {winner['yes_bid']}")
            print(f"Final Yes ask: {winner['yes_ask']}")

    print("\n=== All Market Ranges ===")
    for market in sorted(markets, key=lambda x: x.get('subtitle', '')):
        result_indicator = " ✓" if market.get('result') == 'yes' else ""
        print(f"{market['subtitle']}: {market['ticker']}{result_indicator}")

    # Try to get historical prices for one market
    if markets:
        test_ticker = markets[0]['ticker']
        print(f"\n=== Testing price history for {test_ticker} ===")
        history_response = requests.get(f"{base_url}/markets/{test_ticker}/history")
        print(f"History endpoint status: {history_response.status_code}")
        if history_response.status_code == 200:
            print("Price history available!")
            history = history_response.json()
            print(f"Keys: {history.keys()}")
        else:
            print(f"Error: {history_response.text[:200]}")

else:
    print(f"Error: {response.status_code}")
    print(response.text)
