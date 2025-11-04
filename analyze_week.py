"""
Analyze one week of collected trading data
Run this after collecting 7 days of data
"""
import json
import requests
from datetime import datetime
from typing import List, Dict
from collections import defaultdict
import statistics


class WeekAnalyzer:
    """Analyze a week of trading data"""

    BASE_URL = "https://api.elections.kalshi.com/trade-api/v2"
    NYC_LAT = 40.7128
    NYC_LON = -74.0060

    def __init__(self, trades_file: str = "data/trades.json"):
        self.trades_file = trades_file

    def load_trades(self) -> List[Dict]:
        """Load trades from JSON"""
        try:
            with open(self.trades_file, 'r') as f:
                return json.load(f)
        except FileNotFoundError:
            print(f"Error: {self.trades_file} not found")
            return []

    def get_actual_temp(self, date_str: str) -> float:
        """Get actual temperature"""
        url = "https://archive-api.open-meteo.com/v1/archive"
        params = {
            'latitude': self.NYC_LAT,
            'longitude': self.NYC_LON,
            'start_date': date_str,
            'end_date': date_str,
            'daily': 'temperature_2m_max',
            'temperature_unit': 'fahrenheit',
            'timezone': 'America/New_York'
        }

        response = requests.get(url, params=params, timeout=10)
        if response.status_code == 200:
            data = response.json()
            return data['daily']['temperature_2m_max'][0]
        return None

    def get_winning_market(self, date_str: str) -> str:
        """Get winning market"""
        date_obj = datetime.fromisoformat(date_str)
        event_ticker = f"KXHIGHNY-{date_obj.strftime('%y%b%d').upper()}"

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

    def analyze(self):
        """Perform comprehensive analysis"""
        trades = self.load_trades()

        if not trades:
            print("No trades to analyze")
            return

        print("="*70)
        print(" "*25 + "WEEK ANALYSIS")
        print("="*70)
        print(f"\nData collection period: {trades[0]['date']} to {trades[-1]['date']}")
        print(f"Total days collected: {len(trades)}\n")

        # Evaluate each trade
        results = []
        errors_by_day = []

        for trade in trades:
            date_str = trade['date']
            days_ago = (datetime.now() - datetime.fromisoformat(date_str)).days

            if days_ago < 1:
                print(f"⏳ {date_str}: Market not yet settled")
                continue

            actual_temp = self.get_actual_temp(date_str)
            winning_market = self.get_winning_market(date_str)

            if actual_temp and winning_market:
                won = trade['market_subtitle'] == winning_market
                error = abs(trade['forecast_temp'] - actual_temp)

                results.append({
                    'date': date_str,
                    'forecast': trade['forecast_temp'],
                    'actual': actual_temp,
                    'predicted_market': trade['market_subtitle'],
                    'winning_market': winning_market,
                    'won': won,
                    'error': error,
                    'confidence': trade.get('confidence', 0.0)
                })

                errors_by_day.append(error)

                status = "✓ WIN " if won else "✗ LOSS"
                print(f"{date_str}: {status} | Forecast: {trade['forecast_temp']:.1f}°F | Actual: {actual_temp:.1f}°F | Error: {error:.1f}°F")

        if not results:
            print("\nNo settled trades to analyze yet")
            return

        # Calculate statistics
        print("\n" + "="*70)
        print("PERFORMANCE STATISTICS")
        print("="*70)

        total = len(results)
        wins = sum(1 for r in results if r['won'])
        win_rate = wins / total

        print(f"\nOverall Performance:")
        print(f"  Total settled trades: {total}")
        print(f"  Wins: {wins}")
        print(f"  Losses: {total - wins}")
        print(f"  Win rate: {win_rate:.1%}")

        # Error analysis
        print(f"\nForecast Accuracy:")
        print(f"  Average error: {statistics.mean(errors_by_day):.2f}°F")
        print(f"  Median error: {statistics.median(errors_by_day):.2f}°F")
        print(f"  Min error: {min(errors_by_day):.2f}°F")
        print(f"  Max error: {max(errors_by_day):.2f}°F")
        if len(errors_by_day) > 1:
            print(f"  Std deviation: {statistics.stdev(errors_by_day):.2f}°F")

        # Confidence analysis
        high_conf = [r for r in results if r['confidence'] >= 0.8]
        med_conf = [r for r in results if 0.6 <= r['confidence'] < 0.8]
        low_conf = [r for r in results if r['confidence'] < 0.6]

        print(f"\nConfidence Levels:")
        if high_conf:
            high_wins = sum(1 for r in high_conf if r['won'])
            print(f"  High (≥80%): {high_wins}/{len(high_conf)} = {high_wins/len(high_conf):.1%}")
        if med_conf:
            med_wins = sum(1 for r in med_conf if r['won'])
            print(f"  Medium (60-80%): {med_wins}/{len(med_conf)} = {med_wins/len(med_conf):.1%}")
        if low_conf:
            low_wins = sum(1 for r in low_conf if r['won'])
            print(f"  Low (<60%): {low_wins}/{len(low_conf)} = {low_wins/len(low_conf):.1%}")

        # Day-of-week analysis
        dow_stats = defaultdict(lambda: {'wins': 0, 'total': 0})
        for r in results:
            date_obj = datetime.fromisoformat(r['date'])
            dow = date_obj.strftime('%A')
            dow_stats[dow]['total'] += 1
            if r['won']:
                dow_stats[dow]['wins'] += 1

        print(f"\nDay of Week Analysis:")
        for day in ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']:
            if day in dow_stats:
                stats = dow_stats[day]
                wr = stats['wins'] / stats['total']
                print(f"  {day}: {stats['wins']}/{stats['total']} = {wr:.1%}")

        # Temperature range analysis
        temp_ranges = {
            'Cold (<55°F)': [r for r in results if r['actual'] < 55],
            'Mild (55-65°F)': [r for r in results if 55 <= r['actual'] < 65],
            'Warm (65-75°F)': [r for r in results if 65 <= r['actual'] < 75],
            'Hot (≥75°F)': [r for r in results if r['actual'] >= 75]
        }

        print(f"\nTemperature Range Performance:")
        for range_name, range_results in temp_ranges.items():
            if range_results:
                range_wins = sum(1 for r in range_results if r['won'])
                range_total = len(range_results)
                range_wr = range_wins / range_total
                avg_error = statistics.mean([r['error'] for r in range_results])
                print(f"  {range_name}: {range_wins}/{range_total} = {range_wr:.1%} (avg error: {avg_error:.2f}°F)")

        # Profitability estimate
        print("\n" + "="*70)
        print("PROFITABILITY ANALYSIS")
        print("="*70)

        for entry_price in [0.40, 0.45, 0.50]:
            profit_per_win = 1.0 - entry_price
            loss_per_trade = entry_price
            total_profit = (wins * profit_per_win) - ((total - wins) * loss_per_trade)
            roi = (total_profit / (total * entry_price)) * 100

            print(f"\nAt {entry_price*100:.0f}¢ entry price:")
            print(f"  Profit per win: ${profit_per_win:.2f}")
            print(f"  Total profit: ${total_profit:.2f}")
            print(f"  ROI: {roi:.1f}%")

        # Recommendations
        print("\n" + "="*70)
        print("RECOMMENDATIONS")
        print("="*70)

        recommendations = []

        if win_rate < 0.2:
            recommendations.append("⚠ Win rate below 20% - consider adjusting forecast sources or strategy")
        elif win_rate > 0.4:
            recommendations.append("✓ Win rate above 40% - excellent performance!")

        avg_error = statistics.mean(errors_by_day)
        if avg_error > 2.0:
            recommendations.append("⚠ High forecast error - consider adding more forecast sources")
        elif avg_error < 1.0:
            recommendations.append("✓ Low forecast error - forecasts are very accurate")

        if high_conf and len(high_conf) >= 2:
            high_wr = sum(1 for r in high_conf if r['won']) / len(high_conf)
            if high_wr > win_rate * 1.2:
                recommendations.append("✓ High confidence trades perform better - consider only trading when confidence >80%")

        if not recommendations:
            recommendations.append("✓ Continue current strategy and collect more data")

        for i, rec in enumerate(recommendations, 1):
            print(f"\n{i}. {rec}")

        print("\n" + "="*70)
        print()


if __name__ == "__main__":
    analyzer = WeekAnalyzer()
    analyzer.analyze()
