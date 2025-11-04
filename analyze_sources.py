"""
Analyze individual forecast source accuracy
Determines which weather service is most accurate for NYC
"""
import json
import requests
from datetime import datetime
from typing import List, Dict
from collections import defaultdict
import statistics


class SourceAnalyzer:
    """Analyze accuracy of individual forecast sources"""

    NYC_LAT = 40.7128
    NYC_LON = -74.0060

    def __init__(self, trades_file: str = "data/trades.json"):
        self.trades_file = trades_file

    def load_trades(self) -> List[Dict]:
        """Load trades with individual forecast data"""
        try:
            with open(self.trades_file, 'r') as f:
                return json.load(f)
        except FileNotFoundError:
            print(f"Error: {self.trades_file} not found")
            return []

    def get_actual_temp(self, date_str: str) -> float:
        """Get actual temperature from archive"""
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

    def analyze(self):
        """Analyze source accuracy"""
        trades = self.load_trades()

        if not trades:
            print("No trades to analyze")
            return

        # Skip trades without individual forecast data
        trades_with_sources = [t for t in trades if 'individual_forecasts' in t]

        if not trades_with_sources:
            print("No trades with individual forecast data")
            print("This feature was added after your first trades.")
            print("New trades will include this data.")
            return

        print("="*70)
        print(" "*20 + "FORECAST SOURCE ANALYSIS")
        print("="*70)
        print(f"\nAnalyzing {len(trades_with_sources)} trades with source data...\n")

        # Track errors by source
        source_errors = defaultdict(list)
        source_forecasts = defaultdict(list)
        source_availability = defaultdict(int)

        for trade in trades_with_sources:
            date_str = trade['date']
            days_ago = (datetime.now() - datetime.fromisoformat(date_str)).days

            if days_ago < 1:
                continue  # Skip unsettled trades

            actual_temp = self.get_actual_temp(date_str)
            if not actual_temp:
                continue

            forecasts = trade.get('individual_forecasts', {})

            for source, forecast_temp in forecasts.items():
                error = abs(forecast_temp - actual_temp)
                source_errors[source].append(error)
                source_forecasts[source].append({
                    'date': date_str,
                    'forecast': forecast_temp,
                    'actual': actual_temp,
                    'error': error
                })
                source_availability[source] += 1

        if not source_errors:
            print("No settled trades with source data yet")
            return

        # Calculate statistics for each source
        results = []
        for source in source_errors.keys():
            errors = source_errors[source]
            avg_error = statistics.mean(errors)
            median_error = statistics.median(errors)
            std_dev = statistics.stdev(errors) if len(errors) > 1 else 0
            availability = source_availability[source]

            results.append({
                'source': source,
                'avg_error': avg_error,
                'median_error': median_error,
                'std_dev': std_dev,
                'availability': availability,
                'forecasts': source_forecasts[source]
            })

        # Sort by average error (best first)
        results.sort(key=lambda x: x['avg_error'])

        # Print rankings
        print("ACCURACY RANKINGS (Lower error = Better)")
        print("-" * 70)
        print(f"{'Rank':<6}{'Source':<20}{'Avg Error':<15}{'Median':<15}{'Std Dev':<15}")
        print("-" * 70)

        for i, result in enumerate(results, 1):
            rank_symbol = "🥇" if i == 1 else "🥈" if i == 2 else "🥉" if i == 3 else f"{i}."
            print(f"{rank_symbol:<6}{result['source']:<20}"
                  f"{result['avg_error']:.2f}°F{'':<8}"
                  f"{result['median_error']:.2f}°F{'':<8}"
                  f"{result['std_dev']:.2f}°F")

        # Detailed analysis
        print("\n" + "="*70)
        print("DETAILED SOURCE ANALYSIS")
        print("="*70)

        for result in results:
            print(f"\n{result['source']}")
            print("-" * 40)
            print(f"  Days available: {result['availability']}")
            print(f"  Average error: {result['avg_error']:.2f}°F")
            print(f"  Median error: {result['median_error']:.2f}°F")
            print(f"  Std deviation: {result['std_dev']:.2f}°F")
            print(f"  Min error: {min(f['error'] for f in result['forecasts']):.2f}°F")
            print(f"  Max error: {max(f['error'] for f in result['forecasts']):.2f}°F")

            # Show bias (over/under forecasting)
            biases = [f['forecast'] - f['actual'] for f in result['forecasts']]
            avg_bias = statistics.mean(biases)
            if abs(avg_bias) > 0.5:
                tendency = "over-forecasts" if avg_bias > 0 else "under-forecasts"
                print(f"  Bias: {tendency} by {abs(avg_bias):.2f}°F on average")

        # Recommendations
        print("\n" + "="*70)
        print("RECOMMENDATIONS")
        print("="*70)

        best = results[0]
        worst = results[-1]

        print(f"\n🏆 Best performer: {best['source']}")
        print(f"   Average error: {best['avg_error']:.2f}°F")

        if worst['avg_error'] > best['avg_error'] * 1.5:
            print(f"\n⚠️  Worst performer: {worst['source']}")
            print(f"   Average error: {worst['avg_error']:.2f}°F")
            print(f"   Consider reducing weight or removing this source")

        # Check if user's MSN hypothesis is validated
        if 'MSN' in [r['source'] for r in results]:
            msn_result = next(r for r in results if r['source'] == 'MSN')
            msn_rank = results.index(msn_result) + 1

            print(f"\n📊 MSN Weather performance:")
            print(f"   Rank: #{msn_rank} out of {len(results)}")
            print(f"   Average error: {msn_result['avg_error']:.2f}°F")

            if msn_rank == 1:
                print("   ✓ Your research was correct - MSN is the best!")
                print("   Continue prioritizing MSN in consensus calculation")
            elif msn_rank <= len(results) // 2:
                print("   MSN performs above average - current weighting is good")
            else:
                print("   ⚠️ MSN underperforming - consider adjusting weight")

        # Suggest weight adjustments
        print(f"\n💡 Suggested source weights:")
        for i, result in enumerate(results, 1):
            if i == 1:
                weight = 2.0
            elif i == 2:
                weight = 1.5
            elif result['avg_error'] < 1.5:
                weight = 1.0
            else:
                weight = 0.5

            print(f"   {result['source']}: {weight}x")

        print("\n" + "="*70)


if __name__ == "__main__":
    analyzer = SourceAnalyzer()
    analyzer.analyze()
