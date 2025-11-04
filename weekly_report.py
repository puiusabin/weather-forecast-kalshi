"""
Master weekly report - runs all analyses and provides actionable recommendations
Run this every Sunday after a week of data collection
"""
import json
from datetime import datetime
from analyze_week import WeekAnalyzer
from analyze_sources import SourceAnalyzer
from analyze_patterns import PatternAnalyzer
from strategy_optimizer import StrategyOptimizer


class WeeklyReport:
    """Generate comprehensive weekly report with all analyses"""

    def __init__(self, trades_file: str = "data/trades.json"):
        self.trades_file = trades_file
        self.week_analyzer = WeekAnalyzer(trades_file)
        self.source_analyzer = SourceAnalyzer(trades_file)
        self.pattern_analyzer = PatternAnalyzer(trades_file)
        self.strategy_optimizer = StrategyOptimizer(trades_file)

    def generate_header(self):
        """Generate report header"""
        print("\n")
        print("="*80)
        print(" "*25 + "WEEKLY TRADING REPORT")
        print(" "*28 + f"{datetime.now().strftime('%B %d, %Y')}")
        print("="*80)

    def generate_executive_summary(self):
        """High-level summary of the week"""
        print("\n" + "="*80)
        print("EXECUTIVE SUMMARY")
        print("="*80)

        trades = self.week_analyzer.load_trades()

        if not trades:
            print("\nNo data collected yet. Start Docker container and collect for 7 days.")
            return False

        # Basic stats
        total = len(trades)
        latest = trades[-1]['date'] if trades else "N/A"
        oldest = trades[0]['date'] if trades else "N/A"

        print(f"\nData collection period: {oldest} to {latest}")
        print(f"Total days of data: {total}")

        # Check if we have comprehensive logging
        comprehensive = sum(1 for t in trades if 'log_version' in t)
        print(f"Days with comprehensive logging: {comprehensive}/{total}")

        if comprehensive < total:
            print(f"\n⚠️  Upgrade needed: Rebuild container to get comprehensive logging")
            print(f"   Run: sudo docker-compose down && sudo docker-compose up -d --build")

        return True

    def generate_action_items(self):
        """Generate specific action items for next week"""
        print("\n" + "="*80)
        print("ACTION ITEMS FOR NEXT WEEK")
        print("="*80)

        trades = self.week_analyzer.load_trades()
        actions = []

        # Check data quality
        comprehensive = sum(1 for t in trades if 'log_version' in t)
        if comprehensive < len(trades):
            actions.append({
                'priority': 'HIGH',
                'action': 'Rebuild Docker container with latest code',
                'reason': 'Missing comprehensive logging on some days',
                'command': 'cd ~/weather-forecast-kalshi && git pull && sudo docker-compose up -d --build'
            })

        # Check source availability
        if comprehensive > 0:
            source_counts = {}
            for t in trades:
                if 'sources_used' in t:
                    for source in t['sources_used']:
                        source_counts[source] = source_counts.get(source, 0) + 1

            if 'MSN' in source_counts and source_counts['MSN'] < len(trades) * 0.7:
                actions.append({
                    'priority': 'MEDIUM',
                    'action': 'Investigate MSN Weather scraping reliability',
                    'reason': f'MSN only available {source_counts.get("MSN", 0)}/{len(trades)} days',
                    'command': 'Check logs: sudo docker exec weather-trader cat /var/log/cron.log | grep MSN'
                })

        # Suggest additional sources if low confidence
        avg_conf = sum(t.get('confidence', 0) for t in trades) / len(trades) if trades else 0
        if avg_conf < 0.7:
            actions.append({
                'priority': 'MEDIUM',
                'action': 'Add more forecast sources',
                'reason': f'Average confidence only {avg_conf:.1%}',
                'command': 'Get API keys for OpenWeatherMap or WeatherAPI.com'
            })

        # Print actions
        if actions:
            for i, action in enumerate(actions, 1):
                print(f"\n{i}. [{action['priority']}] {action['action']}")
                print(f"   Reason: {action['reason']}")
                if 'command' in action:
                    print(f"   Command: {action['command']}")
        else:
            print("\n✓ No critical actions needed. System running optimally!")
            print("  Continue collecting data and trading.")

    def generate_full_report(self):
        """Generate complete weekly report"""
        self.generate_header()

        if not self.generate_executive_summary():
            return

        print("\n\n")
        print("╔" + "═"*78 + "╗")
        print("║" + " "*25 + "DETAILED ANALYSIS" + " "*36 + "║")
        print("╚" + "═"*78 + "╝")

        # Run all analyses
        try:
            print("\n📊 Overall Performance...")
            self.week_analyzer.analyze()
        except Exception as e:
            print(f"Error in week analysis: {e}")

        try:
            print("\n\n🔬 Forecast Source Comparison...")
            self.source_analyzer.analyze()
        except Exception as e:
            print(f"Error in source analysis: {e}")

        try:
            print("\n\n🔍 Pattern Discovery...")
            self.pattern_analyzer.run_analysis()
        except Exception as e:
            print(f"Error in pattern analysis: {e}")

        try:
            print("\n\n⚙️  Strategy Optimization...")
            self.strategy_optimizer.run()
        except Exception as e:
            print(f"Error in strategy optimization: {e}")

        # Action items
        self.generate_action_items()

        # Footer
        print("\n" + "="*80)
        print(" "*20 + "End of Weekly Report")
        print(" "*15 + "Review, adjust, and trade smarter next week!")
        print("="*80 + "\n")


def main():
    """Generate and display weekly report"""
    report = WeeklyReport()
    report.generate_full_report()


if __name__ == "__main__":
    main()
