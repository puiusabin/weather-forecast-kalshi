"""
Test the REAL risk: Betting too early

Real-world scenario:
1. Morning forecast says max at 2 PM
2. We wait until 2 PM, observe 55°F
3. We bet on "54-55°F" bucket
4. BUT temp goes to 58°F at 4 PM
5. We LOSE

This tests: How often does temp increase significantly AFTER predicted max?
"""
import requests
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from dataclasses import dataclass


@dataclass
class EarlyBettingRisk:
    """Risk assessment for betting before day ends"""
    date: str
    bet_hour: int  # Hour we would place bet
    bet_temp: float  # Observed temp at bet time
    actual_max_temp: float  # Actual daily max
    actual_max_hour: int  # When actual max occurred
    lost_by_betting_early: bool  # Would we lose by betting early?
    temp_increase_after_bet: float  # How much warmer it got after bet


class EarlyBettingTester:
    """Test if betting at various hours risks missing higher temps later"""

    NYC_LAT = 40.7831
    NYC_LON = -73.9712

    def __init__(self):
        self.results = []

    def get_hourly_data(self, target_date: datetime) -> Optional[Dict]:
        """Get hourly temps for a date"""
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
            print(f"Error fetching data: {e}")

        return None

    def test_betting_at_hour(self, target_date: datetime, bet_hour: int) -> Optional[EarlyBettingRisk]:
        """Test what happens if we bet at a specific hour"""
        hourly = self.get_hourly_data(target_date)
        if not hourly:
            return None

        # Get temp at bet hour
        bet_temp = None
        for i, time_str in enumerate(hourly['times']):
            hour = int(time_str[11:13])
            if hour == bet_hour:
                bet_temp = hourly['temps'][i]
                break

        if bet_temp is None:
            return None

        # Find actual daily max
        actual_max = max(t for t in hourly['temps'] if t is not None)
        actual_max_index = hourly['temps'].index(actual_max)
        actual_max_hour = int(hourly['times'][actual_max_index][11:13])

        # Check if betting early caused loss
        bet_bucket = int(bet_temp)
        actual_bucket = int(actual_max)
        lost = (bet_bucket != actual_bucket)

        # How much warmer did it get after bet?
        temp_increase = max(0, actual_max - bet_temp)

        return EarlyBettingRisk(
            date=target_date.strftime('%Y-%m-%d'),
            bet_hour=bet_hour,
            bet_temp=bet_temp,
            actual_max_temp=actual_max,
            actual_max_hour=actual_max_hour,
            lost_by_betting_early=lost,
            temp_increase_after_bet=temp_increase
        )

    def run_analysis(self, days: int = 14, bet_hours: List[int] = [10, 12, 14, 16]) -> Dict:
        """Test betting at different hours across multiple days"""
        print("="*70)
        print("EARLY BETTING RISK ANALYSIS")
        print("="*70)
        print("\nQuestion: What if we bet too early and temp goes higher later?")
        print(f"Testing bet times: {bet_hours}\n")

        end_date = datetime.now() - timedelta(days=1)
        start_date = end_date - timedelta(days=days-1)

        # Test each hour
        results_by_hour = {hour: [] for hour in bet_hours}

        current_date = start_date
        while current_date <= end_date:
            for bet_hour in bet_hours:
                result = self.test_betting_at_hour(current_date, bet_hour)
                if result:
                    results_by_hour[bet_hour].append(result)

            current_date += timedelta(days=1)

        return self.analyze_results(results_by_hour, bet_hours)

    def analyze_results(self, results_by_hour: Dict, bet_hours: List[int]) -> Dict:
        """Analyze results and provide recommendations"""
        print("\n" + "="*70)
        print("RESULTS BY BET TIME")
        print("="*70)

        summary = {}

        for hour in bet_hours:
            results = results_by_hour[hour]
            if not results:
                continue

            total = len(results)
            losses = sum(1 for r in results if r.lost_by_betting_early)
            wins = total - losses
            win_rate = wins / total if total > 0 else 0

            avg_increase = sum(r.temp_increase_after_bet for r in results) / total
            max_increase = max(r.temp_increase_after_bet for r in results)

            print(f"\nBetting at {hour}:00:")
            print(f"  Win rate: {wins}/{total} ({win_rate:.1%})")
            print(f"  Average temp increase after bet: {avg_increase:.1f}°F")
            print(f"  Maximum temp increase: {max_increase:.1f}°F")

            if losses > 0:
                print(f"  ⚠ Lost {losses} times due to betting too early")
                print(f"  Examples of losses:")
                loss_examples = [r for r in results if r.lost_by_betting_early][:3]
                for loss in loss_examples:
                    print(f"    {loss.date}: Bet at {loss.bet_hour}:00 ({loss.bet_temp:.1f}°F), "
                          f"but max was {loss.actual_max_temp:.1f}°F at {loss.actual_max_hour}:00 "
                          f"(+{loss.temp_increase_after_bet:.1f}°F)")

            summary[hour] = {
                'win_rate': win_rate,
                'avg_increase': avg_increase,
                'max_increase': max_increase,
                'losses': losses
            }

        # Find optimal betting time
        print("\n" + "="*70)
        print("OPTIMAL STRATEGY")
        print("="*70)

        best_hour = max(summary.keys(), key=lambda h: summary[h]['win_rate'])
        best_stats = summary[best_hour]

        print(f"\n✓ Best betting time: {best_hour}:00")
        print(f"  Win rate: {best_stats['win_rate']:.1%}")
        print(f"  Risk of temp increase: {best_stats['avg_increase']:.1f}°F average")

        if best_stats['win_rate'] >= 0.85:
            print(f"\n✓ EXCELLENT - Very low risk of betting too early")
        elif best_stats['win_rate'] >= 0.70:
            print(f"\n✓ GOOD - Acceptable risk")
        else:
            print(f"\n⚠ RISKY - High chance of losing due to temp increase")

        print("\n" + "="*70)
        print("STRATEGIC RECOMMENDATIONS")
        print("="*70)

        # Analyze when max temps typically occur
        all_results = []
        for results in results_by_hour.values():
            all_results.extend(results)

        if all_results:
            max_hours = [r.actual_max_hour for r in all_results]
            avg_max_hour = sum(max_hours) / len(max_hours)
            most_common_hour = max(set(max_hours), key=max_hours.count)

            print(f"\n1. Temperature Patterns:")
            print(f"   Average max temp hour: {avg_max_hour:.1f}:00")
            print(f"   Most common max hour: {most_common_hour}:00")

            early_max = sum(1 for h in max_hours if h <= 12)
            late_max = sum(1 for h in max_hours if h > 12)

            print(f"   Early max (≤12:00): {early_max}/{len(max_hours)} days ({early_max/len(max_hours):.1%})")
            print(f"   Late max (>12:00): {late_max}/{len(max_hours)} days ({late_max/len(max_hours):.1%})")

        print(f"\n2. Risk Mitigation:")
        print(f"   - Check morning forecast for predicted max time")
        print(f"   - If max predicted early (≤12:00), safer to bet sooner")
        print(f"   - If max predicted late (≥15:00), wait until that time")
        print(f"   - Add 1-2 hour buffer after forecast max time to be safe")

        print(f"\n3. Optimal Workflow:")
        print(f"   9 AM: Check hourly forecast, note predicted max time")
        print(f"   Wait until: (Predicted max time) + 1 hour")
        print(f"   Then: Get NWS observation and place bet")
        print(f"   Markets close: ~4 AM next day (plenty of time)")

        return summary


def main():
    """Run the early betting risk test"""
    tester = EarlyBettingTester()

    # Test betting at different times of day
    tester.run_analysis(days=14, bet_hours=[10, 12, 14, 16, 18])


if __name__ == "__main__":
    main()
