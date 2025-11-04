"""
Advanced pattern analysis using comprehensive logging data
Discovers insights from detailed data collection
"""
import json
from datetime import datetime
from typing import List, Dict
from collections import defaultdict
import statistics


class PatternAnalyzer:
    """Analyze patterns in comprehensive trading data"""

    def __init__(self, trades_file: str = "data/trades.json"):
        self.trades_file = trades_file

    def load_trades(self) -> List[Dict]:
        """Load comprehensive trade data"""
        try:
            with open(self.trades_file, 'r') as f:
                return json.load(f)
        except FileNotFoundError:
            print(f"Error: {self.trades_file} not found")
            return []

    def analyze_day_of_week_patterns(self, trades: List[Dict]):
        """Are certain days more predictable?"""
        print("\n" + "="*70)
        print("DAY OF WEEK ANALYSIS")
        print("="*70)

        dow_stats = defaultdict(lambda: {'count': 0, 'avg_confidence': [], 'sources': []})

        for trade in trades:
            if 'day_of_week' not in trade:
                continue

            dow = trade['day_of_week']
            dow_stats[dow]['count'] += 1
            dow_stats[dow]['avg_confidence'].append(trade.get('confidence', 0))
            dow_stats[dow]['sources'].append(trade.get('num_sources', 0))

        for day in ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']:
            if day in dow_stats:
                stats = dow_stats[day]
                avg_conf = statistics.mean(stats['avg_confidence'])
                avg_sources = statistics.mean(stats['sources'])

                print(f"\n{day}:")
                print(f"  Trades: {stats['count']}")
                print(f"  Avg confidence: {avg_conf:.1%}")
                print(f"  Avg sources available: {avg_sources:.1f}")

    def analyze_weather_trends(self, trades: List[Dict]):
        """Does trend (warming/cooling) affect accuracy?"""
        print("\n" + "="*70)
        print("WEATHER TREND ANALYSIS")
        print("="*70)

        trend_stats = defaultdict(lambda: {'count': 0, 'confidences': []})

        for trade in trades:
            if 'weather_context' not in trade or not trade['weather_context']:
                continue

            trend = trade['weather_context'].get('trend', 'unknown')
            trend_stats[trend]['count'] += 1
            trend_stats[trend]['confidences'].append(trade.get('confidence', 0))

        for trend, stats in trend_stats.items():
            if stats['count'] > 0:
                avg_conf = statistics.mean(stats['confidences'])
                print(f"\n{trend.capitalize()} trend:")
                print(f"  Days: {stats['count']}")
                print(f"  Avg confidence: {avg_conf:.1%}")

    def analyze_source_combinations(self, trades: List[Dict]):
        """Which source combinations work best?"""
        print("\n" + "="*70)
        print("SOURCE COMBINATION ANALYSIS")
        print("="*70)

        combo_stats = defaultdict(lambda: {'count': 0, 'confidences': []})

        for trade in trades:
            if 'sources_used' not in trade:
                continue

            sources = tuple(sorted(trade['sources_used']))
            combo_stats[sources]['count'] += 1
            combo_stats[sources]['confidences'].append(trade.get('confidence', 0))

        # Sort by frequency
        sorted_combos = sorted(combo_stats.items(), key=lambda x: x[1]['count'], reverse=True)

        for sources, stats in sorted_combos[:5]:  # Top 5
            avg_conf = statistics.mean(stats['confidences'])
            print(f"\n{' + '.join(sources)}:")
            print(f"  Times used: {stats['count']}")
            print(f"  Avg confidence: {avg_conf:.1%}")

    def analyze_market_proximity(self, trades: List[Dict]):
        """Are we picking markets on the edge or center of forecast?"""
        print("\n" + "="*70)
        print("MARKET PROXIMITY ANALYSIS")
        print("="*70)

        distances = []

        for trade in trades:
            if 'market_analysis' not in trade:
                continue

            ma = trade['market_analysis']
            if 'selected_market' in ma and ma['selected_market']:
                dist = ma['selected_market'].get('distance_from_forecast', 0)
                distances.append(dist)

        if distances:
            print(f"\nAverage distance to selected market midpoint: {statistics.mean(distances):.2f}°F")
            print(f"Median distance: {statistics.median(distances):.2f}°F")
            print(f"Min distance: {min(distances):.2f}°F")
            print(f"Max distance: {max(distances):.2f}°F")

            close_calls = sum(1 for d in distances if d > 0.5)
            print(f"\nClose calls (>0.5°F from midpoint): {close_calls}/{len(distances)}")

    def analyze_confidence_agreement(self, trades: List[Dict]):
        """How does source agreement affect confidence?"""
        print("\n" + "="*70)
        print("CONFIDENCE VS SOURCE AGREEMENT")
        print("="*70)

        agreement_buckets = {
            'high': {'confidences': [], 'count': 0},    # >80% sources agree
            'medium': {'confidences': [], 'count': 0},  # 50-80% agree
            'low': {'confidences': [], 'count': 0}      # <50% agree
        }

        for trade in trades:
            if 'confidence_breakdown' not in trade:
                continue

            cb = trade['confidence_breakdown']
            agreement_rate = cb.get('agreement_rate', 0)

            if agreement_rate >= 0.8:
                bucket = 'high'
            elif agreement_rate >= 0.5:
                bucket = 'medium'
            else:
                bucket = 'low'

            agreement_buckets[bucket]['count'] += 1
            agreement_buckets[bucket]['confidences'].append(trade.get('confidence', 0))

        for level, data in agreement_buckets.items():
            if data['count'] > 0:
                avg_conf = statistics.mean(data['confidences'])
                print(f"\n{level.capitalize()} source agreement:")
                print(f"  Days: {data['count']}")
                print(f"  Avg confidence: {avg_conf:.1%}")

    def analyze_time_of_day(self, trades: List[Dict]):
        """Does forecast time matter?"""
        print("\n" + "="*70)
        print("TIME OF DAY ANALYSIS")
        print("="*70)

        times = []
        for trade in trades:
            if 'forecast_time' in trade:
                times.append(trade['forecast_time'])

        if times:
            print(f"\nForecast times: {', '.join(times)}")
            print(f"Most common: {max(set(times), key=times.count)}")

    def find_optimal_thresholds(self, trades: List[Dict]):
        """What confidence threshold should we use?"""
        print("\n" + "="*70)
        print("OPTIMAL CONFIDENCE THRESHOLD")
        print("="*70)

        if not trades:
            return

        confidences = [t.get('confidence', 0) for t in trades]

        if confidences:
            print(f"\nConfidence statistics:")
            print(f"  Average: {statistics.mean(confidences):.1%}")
            print(f"  Median: {statistics.median(confidences):.1%}")
            print(f"  Min: {min(confidences):.1%}")
            print(f"  Max: {max(confidences):.1%}")

            # Suggest threshold
            suggested = statistics.median(confidences)
            print(f"\n💡 Suggested minimum confidence threshold: {suggested:.1%}")
            print(f"   This would filter out {sum(1 for c in confidences if c < suggested)} trades")

    def run_analysis(self):
        """Run all pattern analyses"""
        print("="*70)
        print(" "*20 + "PATTERN ANALYSIS")
        print("="*70)

        trades = self.load_trades()

        if not trades:
            print("\nNo trades to analyze")
            return

        # Filter to trades with comprehensive logging
        comprehensive_trades = [t for t in trades if 'log_version' in t]

        if not comprehensive_trades:
            print("\nNo trades with comprehensive logging yet")
            print("Rebuild container and collect new data to enable pattern analysis")
            return

        print(f"\nAnalyzing {len(comprehensive_trades)} trades with comprehensive data\n")

        self.analyze_day_of_week_patterns(comprehensive_trades)
        self.analyze_weather_trends(comprehensive_trades)
        self.analyze_source_combinations(comprehensive_trades)
        self.analyze_market_proximity(comprehensive_trades)
        self.analyze_confidence_agreement(comprehensive_trades)
        self.analyze_time_of_day(comprehensive_trades)
        self.find_optimal_thresholds(comprehensive_trades)

        print("\n" + "="*70)


if __name__ == "__main__":
    analyzer = PatternAnalyzer()
    analyzer.run_analysis()
