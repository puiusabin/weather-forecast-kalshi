"""
Track trading performance over time
"""
import json
import requests
from datetime import datetime
from typing import List, Dict
from dataclasses import dataclass


@dataclass
class TradeResult:
    """Result of a single trade"""
    date: str
    forecast_temp: float
    predicted_market: str
    actual_temp: float
    winning_market: str
    won: bool
    confidence: float


class PerformanceTracker:
    """Track and analyze trading performance"""

    BASE_URL = "https://api.elections.kalshi.com/trade-api/v2"
    NYC_LAT = 40.7128
    NYC_LON = -74.0060

    def __init__(self, trades_file: str = "trades.json"):
        self.trades_file = trades_file

    def load_trades(self) -> List[Dict]:
        """Load trades from JSON file"""
        try:
            with open(self.trades_file, 'r') as f:
                return json.load(f)
        except FileNotFoundError:
            return []

    def get_actual_temp(self, date: datetime) -> float:
        """Get actual temperature from Open-Meteo archive"""
        url = "https://archive-api.open-meteo.com/v1/archive"
        params = {
            'latitude': self.NYC_LAT,
            'longitude': self.NYC_LON,
            'start_date': date.strftime('%Y-%m-%d'),
            'end_date': date.strftime('%Y-%m-%d'),
            'daily': 'temperature_2m_max',
            'temperature_unit': 'fahrenheit',
            'timezone': 'America/New_York'
        }

        response = requests.get(url, params=params, timeout=10)
        if response.status_code == 200:
            data = response.json()
            return data['daily']['temperature_2m_max'][0]
        return None

    def get_winning_market(self, date: datetime) -> str:
        """Get the winning market for a specific date"""
        event_ticker = f"KXHIGHNY-{date.strftime('%y%b%d').upper()}"

        response = requests.get(
            f"{self.BASE_URL}/markets",
            params={'event_ticker': event_ticker, 'limit': 20}
        )

        if response.status_code == 200:
            markets = response.json().get('markets', [])
            for market in markets:
                if market.get('result') == 'yes':
                    return market['subtitle']
        return None

    def evaluate_trades(self) -> List[TradeResult]:
        """Evaluate all completed trades"""
        trades = self.load_trades()
        results = []

        for trade in trades:
            trade_date = datetime.fromisoformat(trade['date'])

            # Skip if trade is too recent (market not settled)
            days_ago = (datetime.now() - trade_date).days
            if days_ago < 1:
                print(f"Skipping {trade['date']} (not yet settled)")
                continue

            # Get actual results
            actual_temp = self.get_actual_temp(trade_date)
            winning_market = self.get_winning_market(trade_date)

            if actual_temp and winning_market:
                won = trade['market_subtitle'] == winning_market

                result = TradeResult(
                    date=trade['date'],
                    forecast_temp=trade['forecast_temp'],
                    predicted_market=trade['market_subtitle'],
                    actual_temp=actual_temp,
                    winning_market=winning_market,
                    won=won,
                    confidence=trade.get('confidence', 0.0)
                )

                results.append(result)

                status = "✓ WIN " if won else "✗ LOSS"
                error = abs(trade['forecast_temp'] - actual_temp)
                print(f"{trade['date']}: {status} | Predicted: {trade['market_subtitle']} | Actual: {winning_market} (Error: {error:.1f}°F)")

        return results

    def calculate_stats(self, results: List[TradeResult]):
        """Calculate and print statistics"""
        if not results:
            print("\nNo completed trades to analyze")
            return

        total = len(results)
        wins = sum(1 for r in results if r.won)
        losses = total - wins
        win_rate = wins / total

        errors = [abs(r.forecast_temp - r.actual_temp) for r in results]
        avg_error = sum(errors) / len(errors)

        # Calculate by confidence level
        high_conf = [r for r in results if r.confidence >= 0.8]
        med_conf = [r for r in results if 0.6 <= r.confidence < 0.8]
        low_conf = [r for r in results if r.confidence < 0.6]

        print(f"\n{'='*60}")
        print("PERFORMANCE SUMMARY")
        print(f"{'='*60}")
        print(f"Total Trades: {total}")
        print(f"Wins: {wins}")
        print(f"Losses: {losses}")
        print(f"Win Rate: {win_rate:.1%}")
        print(f"Average Forecast Error: {avg_error:.2f}°F")

        if high_conf:
            high_wins = sum(1 for r in high_conf if r.won)
            print(f"\nHigh Confidence (≥80%): {high_wins}/{len(high_conf)} = {high_wins/len(high_conf):.1%}")

        if med_conf:
            med_wins = sum(1 for r in med_conf if r.won)
            print(f"Medium Confidence (60-80%): {med_wins}/{len(med_conf)} = {med_wins/len(med_conf):.1%}")

        if low_conf:
            low_wins = sum(1 for r in low_conf if r.won)
            print(f"Low Confidence (<60%): {low_wins}/{len(low_conf)} = {low_wins/len(low_conf):.1%}")

        print(f"{'='*60}\n")

        # Profitability estimate (assuming 45 cent entry)
        avg_entry_price = 0.45  # 45 cents per contract
        profit_per_win = 1.0 - avg_entry_price  # 55 cents
        loss_per_trade = avg_entry_price  # 45 cents

        total_profit = (wins * profit_per_win) - (losses * loss_per_trade)
        roi = (total_profit / (total * avg_entry_price)) * 100

        print("PROFITABILITY ESTIMATE (assuming 45¢ entry price):")
        print(f"  Profit per win: {profit_per_win*100:.0f}¢")
        print(f"  Loss per trade: {loss_per_trade*100:.0f}¢")
        print(f"  Net profit: ${total_profit:.2f}")
        print(f"  ROI: {roi:.1f}%\n")


def main():
    """Main performance tracking"""
    print("="*60)
    print("PERFORMANCE TRACKER")
    print("="*60 + "\n")

    tracker = PerformanceTracker()
    results = tracker.evaluate_trades()
    tracker.calculate_stats(results)


if __name__ == "__main__":
    main()
