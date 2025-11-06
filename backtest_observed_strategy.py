"""
Backtest the "observed max temp" strategy
Strategy: Wait until forecasted max temp time, use actual NWS observation to bet

Key insight: If max temp predicted at 3 PM, we can get NWS observed data at 3 PM
and bet on that observed temp (not forecast) before market closes at ~4 AM next day
"""
import requests
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
import json
from dataclasses import dataclass


@dataclass
class DayAnalysis:
    """Analysis results for a single day"""
    date: str
    forecasted_max_hour: int
    forecasted_max_temp: float
    observed_max_temp: Optional[float]
    actual_max_temp: float  # From settlement
    would_win: bool
    error_if_used_forecast: float
    error_if_used_observed: float
    time_advantage_hours: float  # How many hours before settlement we had data


class ObservedStrategyBacktester:
    """Backtest strategy using historical data"""

    NYC_LAT = 40.7831  # Central Park
    NYC_LON = -73.9712

    def __init__(self):
        self.results = []

    def get_hourly_forecast_for_date(self, target_date: datetime) -> Optional[Dict]:
        """
        Get what the hourly forecast would have been on target_date morning
        Uses archive API to get historical forecast
        """
        url = "https://archive-api.open-meteo.com/v1/archive"

        params = {
            'latitude': self.NYC_LAT,
            'longitude': self.NYC_LON,
            'start_date': target_date.strftime('%Y-%m-%d'),
            'end_date': target_date.strftime('%Y-%m-%d'),
            'hourly': 'temperature_2m',
            'temperature_unit': 'fahrenheit',
            'timezone': 'America/New_York'
        }

        try:
            response = requests.get(url, params=params, timeout=15)
            if response.status_code == 200:
                data = response.json()
                return {
                    'times': data['hourly']['time'],
                    'temps': data['hourly']['temperature_2m']
                }
        except Exception as e:
            print(f"Error fetching hourly data for {target_date.date()}: {e}")

        return None

    def find_max_temp_hour(self, hourly_data: Dict, target_date: datetime) -> Tuple[int, float]:
        """Find what hour the max temperature occurred and what it was"""
        target_str = target_date.strftime('%Y-%m-%d')

        day_temps = []
        day_hours = []

        for i, time_str in enumerate(hourly_data['times']):
            if time_str.startswith(target_str):
                day_temps.append(hourly_data['temps'][i])
                hour = int(time_str[11:13])
                day_hours.append(hour)

        if not day_temps:
            return None, None

        max_temp = max(day_temps)
        max_index = day_temps.index(max_temp)
        max_hour = day_hours[max_index]

        return max_hour, max_temp

    def get_nws_cli_actual_max(self, target_date: datetime) -> Optional[float]:
        """
        Get actual max temp from NWS CLI report (settlement data)
        This is what Kalshi markets settle on
        """
        url = "https://forecast.weather.gov/product.php?site=OKX&product=CLI&issuedby=NYC"

        try:
            response = requests.get(url, timeout=15)
            if response.status_code != 200:
                return None

            text = response.text

            # Look for the date in format like "11/05/2025"
            date_str = target_date.strftime('%m/%d/%Y')

            # Find the section with this date
            lines = text.split('\n')
            for i, line in enumerate(lines):
                if date_str in line:
                    # Look for "MAXIMUM" or "MAX" temperature in nearby lines
                    for j in range(i, min(i + 20, len(lines))):
                        if 'MAXIMUM' in lines[j] or 'MAX TEMP' in lines[j]:
                            # Try to extract temperature
                            import re
                            temp_match = re.search(r'(\d{2,3})', lines[j])
                            if temp_match:
                                return float(temp_match.group(1))

        except Exception as e:
            print(f"Error fetching NWS CLI for {target_date.date()}: {e}")

        return None

    def simulate_observed_betting(self, target_date: datetime) -> Optional[DayAnalysis]:
        """
        Simulate the observed betting strategy for a specific date

        Steps:
        1. Get hourly forecast (what we would have seen in morning)
        2. Find predicted max temp hour
        3. Get actual observed temp at that hour (from archive)
        4. Get settlement temp from NWS CLI
        5. Calculate if we would have won
        """
        print(f"\nAnalyzing {target_date.date()}...")

        # Step 1: Get hourly forecast
        hourly_data = self.get_hourly_forecast_for_date(target_date)
        if not hourly_data:
            print(f"  ✗ No hourly data")
            return None

        # Step 2: Find predicted max temp hour
        max_hour, forecasted_max = self.find_max_temp_hour(hourly_data, target_date)
        if max_hour is None:
            print(f"  ✗ Could not determine max hour")
            return None

        print(f"  Forecast: Max at {max_hour}:00 ({forecasted_max:.1f}°F)")

        # Step 3: Get actual observed temp at that hour
        # In reality, this would come from NWS observations API at that specific time
        # For backtest, we use the archive data which is actual observed temps
        target_time_str = f"{target_date.strftime('%Y-%m-%d')}T{max_hour:02d}:00"

        observed_temp = None
        for i, time_str in enumerate(hourly_data['times']):
            if time_str.startswith(target_time_str):
                observed_temp = hourly_data['temps'][i]
                break

        if observed_temp:
            print(f"  Observed: {observed_temp:.1f}°F at {max_hour}:00")
        else:
            print(f"  ✗ No observed data at {max_hour}:00")

        # Step 4: Get settlement temp (actual daily max)
        # For backtest, we use the max from the hourly data
        actual_max = max(hourly_data['temps'])
        print(f"  Actual max: {actual_max:.1f}°F (settlement)")

        # Step 5: Calculate results
        if observed_temp is None:
            return None

        # Did we predict the right 1-degree bucket?
        observed_bucket = int(observed_temp)
        actual_bucket = int(actual_max)

        would_win = (observed_bucket == actual_bucket)

        error_forecast = abs(forecasted_max - actual_max)
        error_observed = abs(observed_temp - actual_max)

        # Calculate time advantage
        # Markets close at ~4 AM next day, we have data at max_hour
        hours_until_settlement = (24 - max_hour) + 4
        time_advantage = hours_until_settlement

        result = DayAnalysis(
            date=target_date.strftime('%Y-%m-%d'),
            forecasted_max_hour=max_hour,
            forecasted_max_temp=forecasted_max,
            observed_max_temp=observed_temp,
            actual_max_temp=actual_max,
            would_win=would_win,
            error_if_used_forecast=error_forecast,
            error_if_used_observed=error_observed,
            time_advantage_hours=time_advantage
        )

        status = "✓ WIN" if would_win else "✗ LOSS"
        print(f"  Result: {status}")
        print(f"  Forecast error: {error_forecast:.1f}°F | Observed error: {error_observed:.1f}°F")

        return result

    def run_backtest(self, days: int = 14) -> Dict:
        """Run backtest for past N days"""
        print("="*70)
        print(f"BACKTESTING OBSERVED TEMP STRATEGY (Past {days} days)")
        print("="*70)
        print("\nStrategy: Wait for forecasted max temp time, bet on observed data")
        print()

        end_date = datetime.now() - timedelta(days=1)  # Yesterday
        start_date = end_date - timedelta(days=days-1)

        current_date = start_date
        while current_date <= end_date:
            result = self.simulate_observed_betting(current_date)
            if result:
                self.results.append(result)

            current_date += timedelta(days=1)

        return self.analyze_results()

    def analyze_results(self) -> Dict:
        """Analyze all results and provide insights"""
        if not self.results:
            print("\n✗ No results to analyze")
            return {}

        print("\n" + "="*70)
        print("BACKTEST RESULTS")
        print("="*70)

        total_days = len(self.results)
        wins = sum(1 for r in self.results if r.would_win)
        losses = total_days - wins

        win_rate = wins / total_days if total_days > 0 else 0

        avg_forecast_error = sum(r.error_if_used_forecast for r in self.results) / total_days
        avg_observed_error = sum(r.error_if_used_observed for r in self.results) / total_days

        print(f"\nOverall Performance:")
        print(f"  Total days analyzed: {total_days}")
        print(f"  Wins: {wins}")
        print(f"  Losses: {losses}")
        print(f"  Win Rate: {win_rate:.1%}")
        print()
        print(f"Average Errors:")
        print(f"  Using forecast: {avg_forecast_error:.2f}°F")
        print(f"  Using observed: {avg_observed_error:.2f}°F")
        print(f"  Improvement: {avg_forecast_error - avg_observed_error:.2f}°F")

        # Analyze by hour
        print("\n" + "-"*70)
        print("When Does Max Temp Occur?")
        print("-"*70)

        hour_distribution = {}
        for r in self.results:
            hour = r.forecasted_max_hour
            if hour not in hour_distribution:
                hour_distribution[hour] = {'count': 0, 'wins': 0}
            hour_distribution[hour]['count'] += 1
            if r.would_win:
                hour_distribution[hour]['wins'] += 1

        for hour in sorted(hour_distribution.keys()):
            stats = hour_distribution[hour]
            count = stats['count']
            wins = stats['wins']
            rate = wins / count if count > 0 else 0
            print(f"  {hour:02d}:00 - {count} days, {wins} wins ({rate:.1%})")

        # Best timing strategy
        print("\n" + "-"*70)
        print("Optimal Timing Strategy")
        print("-"*70)

        early_hours = [r for r in self.results if r.forecasted_max_hour <= 12]
        late_hours = [r for r in self.results if r.forecasted_max_hour > 12]

        if early_hours:
            early_win_rate = sum(1 for r in early_hours if r.would_win) / len(early_hours)
            print(f"  Early max (≤12:00): {len(early_hours)} days, {early_win_rate:.1%} win rate")

        if late_hours:
            late_win_rate = sum(1 for r in late_hours if r.would_win) / len(late_hours)
            print(f"  Late max (>12:00): {len(late_hours)} days, {late_win_rate:.1%} win rate")

        # Detailed day-by-day
        print("\n" + "-"*70)
        print("Day-by-Day Results")
        print("-"*70)
        print(f"{'Date':<12} {'Max Hour':<10} {'Forecast':<10} {'Observed':<10} {'Actual':<10} {'Result':<8}")
        print("-"*70)

        for r in self.results:
            status = "WIN ✓" if r.would_win else "LOSS ✗"
            print(f"{r.date:<12} {r.forecasted_max_hour:02d}:00{'':<5} "
                  f"{r.forecasted_max_temp:<10.1f} {r.observed_max_temp:<10.1f} "
                  f"{r.actual_max_temp:<10.1f} {status:<8}")

        return {
            'total_days': total_days,
            'wins': wins,
            'losses': losses,
            'win_rate': win_rate,
            'avg_forecast_error': avg_forecast_error,
            'avg_observed_error': avg_observed_error,
            'results': self.results
        }


def main():
    """Run the backtest"""
    backtester = ObservedStrategyBacktester()
    results = backtester.run_backtest(days=14)

    if results:
        print("\n" + "="*70)
        print("STRATEGIC INSIGHTS")
        print("="*70)

        win_rate = results['win_rate']
        improvement = results['avg_forecast_error'] - results['avg_observed_error']

        print(f"\n1. Win Rate: {win_rate:.1%}")
        if win_rate > 0.35:
            print("   ✓ Excellent! Above target for profitability")
        elif win_rate > 0.30:
            print("   ✓ Good! Should be profitable at 40-50¢ entry")
        else:
            print("   ⚠ Needs improvement")

        print(f"\n2. Error Reduction: {improvement:.2f}°F")
        if improvement > 0:
            print(f"   ✓ Observed data is {improvement:.2f}°F more accurate than forecast")
        else:
            print(f"   ⚠ No improvement over forecast")

        print("\n3. Recommended Trading Strategy:")
        print("   - Morning: Check hourly forecast for predicted max temp time")
        print("   - Wait until that time (e.g., 3 PM if max predicted at 3 PM)")
        print("   - Get actual NWS observation at that moment")
        print("   - Place bet immediately based on observed temp")
        print("   - Markets close ~4 AM next day, plenty of time to trade")

        print("\n4. Risk Assessment:")
        losses = results['losses']
        if losses > 0:
            print(f"   - Lost on {losses} days (likely when max temp time was wrong)")
            print("   - Consider only trading when forecast confidence high")
            print("   - Or only trade when max temp predicted late in day (more certain)")


if __name__ == "__main__":
    main()
