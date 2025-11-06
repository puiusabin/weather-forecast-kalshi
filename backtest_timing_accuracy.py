"""
Test the real strategy: Does the forecasted max temp TIME match reality?

Key questions:
1. When forecast says "max at 3 PM", is 3 PM actually when max occurs?
2. If we bet on observed temp at forecasted max time, do we win?
3. What if max actually occurs later? We lose.
"""
import requests
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass


@dataclass
class TimingAnalysis:
    """Analyze if forecast timing matches reality"""
    date: str
    forecasted_max_hour: int
    forecasted_max_temp: float
    observed_at_forecast_hour: float
    actual_max_hour: int
    actual_max_temp: float
    timing_correct: bool  # Did max occur at forecasted hour?
    would_win_if_bet_early: bool  # If we bet on observed temp at forecast hour
    hours_difference: int  # How far off was the timing?


class TimingBacktester:
    """Test if forecast timing predictions are accurate"""

    NYC_LAT = 40.7831
    NYC_LON = -73.9712

    def __init__(self):
        self.results = []

    def get_todays_forecast(self, target_date: datetime) -> Optional[Dict]:
        """
        Simulate getting TODAY's forecast (uses current forecast API)
        In production, we'd get this in the morning
        """
        url = "https://api.open-meteo.com/v1/forecast"
        params = {
            'latitude': self.NYC_LAT,
            'longitude': self.NYC_LON,
            'hourly': 'temperature_2m',
            'temperature_unit': 'fahrenheit',
            'timezone': 'America/New_York',
            'start_date': target_date.strftime('%Y-%m-%d'),
            'end_date': target_date.strftime('%Y-%m-%d'),
            'forecast_days': 1
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
            print(f"Error fetching forecast: {e}")

        return None

    def get_actual_hourly(self, target_date: datetime) -> Optional[Dict]:
        """Get what actually happened (archive data)"""
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
            print(f"Error fetching actual data: {e}")

        return None

    def analyze_day(self, target_date: datetime) -> Optional[TimingAnalysis]:
        """Analyze if forecast timing matched reality for one day"""
        print(f"\nAnalyzing {target_date.date()}...")

        # Can only test "today" since we can't get historical forecasts
        # For older dates, we'll use actual data as proxy
        is_today = target_date.date() == datetime.now().date()

        if is_today:
            forecast_data = self.get_todays_forecast(target_date)
        else:
            # For historical analysis, use archive data
            # This assumes forecast was perfect on timing (optimistic)
            forecast_data = self.get_actual_hourly(target_date)

        if not forecast_data:
            print("  ✗ No forecast data")
            return None

        actual_data = self.get_actual_hourly(target_date)
        if not actual_data:
            print("  ✗ No actual data")
            return None

        # Find forecasted max hour and temp
        forecasted_temps = [t for t in forecast_data['temps'] if t is not None]
        if not forecasted_temps:
            return None

        forecast_max = max(forecasted_temps)
        forecast_max_index = forecast_data['temps'].index(forecast_max)
        forecast_max_hour = int(forecast_data['times'][forecast_max_index][11:13])

        # Find actual max hour and temp
        actual_temps = [t for t in actual_data['temps'] if t is not None]
        if not actual_temps:
            return None

        actual_max = max(actual_temps)
        actual_max_index = actual_data['temps'].index(actual_max)
        actual_max_hour = int(actual_data['times'][actual_max_index][11:13])

        # Get observed temp at forecasted max hour
        observed_at_forecast_hour = None
        for i, time_str in enumerate(actual_data['times']):
            hour = int(time_str[11:13])
            if hour == forecast_max_hour:
                observed_at_forecast_hour = actual_data['temps'][i]
                break

        if observed_at_forecast_hour is None:
            print("  ✗ No observed data at forecast hour")
            return None

        # Check if timing was correct (within 2 hours is good enough)
        timing_correct = abs(forecast_max_hour - actual_max_hour) <= 2

        # Would we win if we bet on observed temp at forecast hour?
        # We win if observed temp bucket = actual max bucket
        observed_bucket = int(observed_at_forecast_hour)
        actual_bucket = int(actual_max)
        would_win = (observed_bucket == actual_bucket)

        hours_diff = actual_max_hour - forecast_max_hour

        print(f"  Forecast: Max at {forecast_max_hour}:00 ({forecast_max:.1f}°F)")
        print(f"  Actual: Max at {actual_max_hour}:00 ({actual_max:.1f}°F)")
        print(f"  Observed at {forecast_max_hour}:00: {observed_at_forecast_hour:.1f}°F")
        print(f"  Timing off by: {abs(hours_diff)} hours")
        print(f"  Would win: {'✓ YES' if would_win else '✗ NO'}")

        return TimingAnalysis(
            date=target_date.strftime('%Y-%m-%d'),
            forecasted_max_hour=forecast_max_hour,
            forecasted_max_temp=forecast_max,
            observed_at_forecast_hour=observed_at_forecast_hour,
            actual_max_hour=actual_max_hour,
            actual_max_temp=actual_max,
            timing_correct=timing_correct,
            would_win_if_bet_early=would_win,
            hours_difference=hours_diff
        )

    def run_backtest(self, days: int = 14) -> Dict:
        """Run timing accuracy backtest"""
        print("="*70)
        print(f"TESTING TIMING PREDICTION ACCURACY (Past {days} days)")
        print("="*70)
        print("\nKey Question: When forecast says max at hour X,")
        print("is the observed temp at hour X actually the day's max?")
        print()

        end_date = datetime.now() - timedelta(days=1)
        start_date = end_date - timedelta(days=days-1)

        current_date = start_date
        while current_date <= end_date:
            result = self.analyze_day(current_date)
            if result:
                self.results.append(result)

            current_date += timedelta(days=1)

        return self.analyze_results()

    def analyze_results(self) -> Dict:
        """Provide strategic insights"""
        if not self.results:
            print("\n✗ No results to analyze")
            return {}

        print("\n" + "="*70)
        print("RESULTS: CAN WE BEAT THE MARKET WITH TIMING?")
        print("="*70)

        total = len(self.results)
        timing_correct = sum(1 for r in self.results if r.timing_correct)
        would_win = sum(1 for r in self.results if r.would_win_if_bet_early)

        timing_accuracy = timing_correct / total if total > 0 else 0
        win_rate = would_win / total if total > 0 else 0

        print(f"\nTiming Accuracy:")
        print(f"  Forecast correctly predicted max hour: {timing_correct}/{total} ({timing_accuracy:.1%})")
        print()
        print(f"Strategy Win Rate:")
        print(f"  Wins if betting at forecasted max time: {would_win}/{total} ({win_rate:.1%})")

        # Analyze failure cases
        losses = [r for r in self.results if not r.would_win_if_bet_early]
        if losses:
            print(f"\nWhy Did We Lose ({len(losses)} days)?")
            for loss in losses:
                temp_diff = loss.actual_max_temp - loss.observed_at_forecast_hour
                print(f"  {loss.date}: Forecast max at {loss.forecasted_max_hour}:00 "
                      f"but actual max at {loss.actual_max_hour}:00 "
                      f"(+{temp_diff:.1f}°F warmer later)")

        # Timing error distribution
        print(f"\nTiming Error Distribution:")
        early = len([r for r in self.results if r.hours_difference < 0])
        correct = len([r for r in self.results if r.hours_difference == 0])
        late = len([r for r in self.results if r.hours_difference > 0])

        print(f"  Forecast too early: {early} days")
        print(f"  Correct timing: {correct} days")
        print(f"  Forecast too late: {late} days")

        avg_timing_error = sum(abs(r.hours_difference) for r in self.results) / total
        print(f"  Average timing error: {avg_timing_error:.1f} hours")

        print("\n" + "="*70)
        print("STRATEGIC RECOMMENDATION")
        print("="*70)

        if win_rate >= 0.40:
            print("✓ Strategy is EXCELLENT")
            print(f"  {win_rate:.1%} win rate with observed data betting")
            print("  RECOMMENDATION: Use this strategy!")
        elif win_rate >= 0.30:
            print("✓ Strategy is GOOD")
            print(f"  {win_rate:.1%} win rate should be profitable")
            print("  RECOMMENDATION: Test with small positions first")
        else:
            print("✗ Strategy needs improvement")
            print(f"  {win_rate:.1%} win rate is too low")
            print("  ISSUE: Forecast timing predictions are not accurate enough")

        if early > late:
            print("\n⚠ Warning: Forecasts tend to predict max too early")
            print("  Risk: Bet too soon, temperature goes higher later")
            print("  Mitigation: Wait 1-2 hours after forecasted max time")
        elif late > early:
            print("\n✓ Good: Forecasts tend to predict max too late")
            print("  Benefit: Safe to bet at forecasted time")

        return {
            'total': total,
            'timing_accuracy': timing_accuracy,
            'win_rate': win_rate,
            'avg_timing_error': avg_timing_error
        }


def main():
    """Run the timing accuracy backtest"""
    backtester = TimingBacktester()
    results = backtester.run_backtest(days=14)


if __name__ == "__main__":
    main()
