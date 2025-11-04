"""
Strategy optimizer based on collected data
Suggests parameter adjustments
"""
import json
from typing import List, Dict, Tuple
from analyze_week import WeekAnalyzer
import statistics


class StrategyOptimizer:
    """Optimize trading strategy based on collected data"""

    def __init__(self, trades_file: str = "data/trades.json"):
        self.analyzer = WeekAnalyzer(trades_file)

    def get_evaluated_results(self) -> List[Dict]:
        """Get all evaluated trade results"""
        trades = self.analyzer.load_trades()
        results = []

        for trade in trades:
            actual = self.analyzer.get_actual_temp(trade['date'])
            winner = self.analyzer.get_winning_market(trade['date'])

            if actual and winner:
                results.append({
                    'date': trade['date'],
                    'forecast': trade['forecast_temp'],
                    'actual': actual,
                    'predicted': trade['market_subtitle'],
                    'winner': winner,
                    'won': trade['market_subtitle'] == winner,
                    'confidence': trade.get('confidence', 0.0),
                    'error': abs(trade['forecast_temp'] - actual)
                })

        return results

    def optimize_confidence_threshold(self, results: List[Dict]) -> Dict:
        """Find optimal confidence threshold"""
        thresholds = [0.5, 0.6, 0.7, 0.8, 0.85, 0.9]
        best_threshold = 0.0
        best_win_rate = 0.0
        best_count = 0

        print("\nConfidence Threshold Optimization:")
        print("="*60)

        for threshold in thresholds:
            filtered = [r for r in results if r['confidence'] >= threshold]
            if filtered:
                wins = sum(1 for r in filtered if r['won'])
                win_rate = wins / len(filtered)

                print(f"Threshold ≥{threshold:.0%}: {wins}/{len(filtered)} = {win_rate:.1%}")

                if win_rate > best_win_rate:
                    best_win_rate = win_rate
                    best_threshold = threshold
                    best_count = len(filtered)

        print(f"\n✓ Optimal threshold: ≥{best_threshold:.0%}")
        print(f"  Win rate: {best_win_rate:.1%}")
        print(f"  Trades: {best_count}")

        return {
            'threshold': best_threshold,
            'win_rate': best_win_rate,
            'count': best_count
        }

    def analyze_forecast_sources(self, results: List[Dict]) -> Dict:
        """Determine which forecast adjustments would help"""
        errors = [r['error'] for r in results]
        avg_error = statistics.mean(errors)

        print("\nForecast Source Analysis:")
        print("="*60)
        print(f"Current avg error: {avg_error:.2f}°F")

        # Analyze bias
        forecast_diffs = [r['forecast'] - r['actual'] for r in results]
        bias = statistics.mean(forecast_diffs)

        if abs(bias) > 0.5:
            direction = "over-forecasting" if bias > 0 else "under-forecasting"
            print(f"⚠ Forecast bias detected: {direction} by {abs(bias):.2f}°F on average")
            print(f"  Recommendation: Apply bias correction of {-bias:.2f}°F")
        else:
            print("✓ No significant forecast bias detected")

        return {
            'avg_error': avg_error,
            'bias': bias
        }

    def suggest_entry_timing(self, results: List[Dict]) -> Dict:
        """Suggest best entry timing based on confidence"""
        # For now, just analyze current data
        # In future, could compare multiple daily runs

        print("\nEntry Timing Analysis:")
        print("="*60)

        if results:
            avg_confidence = statistics.mean([r['confidence'] for r in results])
            print(f"Average confidence at 9 AM: {avg_confidence:.1%}")

            high_conf_count = sum(1 for r in results if r['confidence'] >= 0.8)
            print(f"High confidence trades (≥80%): {high_conf_count}/{len(results)}")

            if avg_confidence < 0.7:
                print("\n💡 Suggestion: Consider checking forecasts later in the morning")
                print("   Forecasts may improve by 11 AM or noon")
            else:
                print("\n✓ Current timing (9 AM) provides good confidence levels")

        return {}

    def generate_config_suggestions(self, results: List[Dict]) -> Dict:
        """Generate configuration suggestions"""
        if not results:
            return {}

        # Optimal threshold
        threshold_opt = self.optimize_confidence_threshold(results)

        # Forecast analysis
        forecast_analysis = self.analyze_forecast_sources(results)

        # Timing
        timing_analysis = self.suggest_entry_timing(results)

        print("\n" + "="*60)
        print("SUGGESTED CONFIGURATION CHANGES")
        print("="*60)

        config = {}

        # Confidence threshold
        if threshold_opt['threshold'] > 0.7:
            config['min_confidence'] = threshold_opt['threshold']
            print(f"\n1. Set minimum confidence threshold: {threshold_opt['threshold']:.0%}")
            print(f"   Only trade when confidence >= {threshold_opt['threshold']:.0%}")

        # Bias correction
        if abs(forecast_analysis['bias']) > 0.5:
            config['bias_correction'] = -forecast_analysis['bias']
            print(f"\n2. Apply bias correction: {-forecast_analysis['bias']:+.2f}°F")
            print(f"   Adjust all forecasts by {-forecast_analysis['bias']:+.2f}°F")

        # Additional sources
        if forecast_analysis['avg_error'] > 1.5:
            print(f"\n3. Add more forecast sources")
            print(f"   Current error: {forecast_analysis['avg_error']:.2f}°F")
            print(f"   Recommendation: Add OpenWeatherMap or other sources")

        if not config:
            print("\n✓ Current configuration is optimal based on available data")

        return config

    def save_optimized_config(self, config: Dict, filename: str = "optimized_config.json"):
        """Save optimized configuration"""
        with open(filename, 'w') as f:
            json.dump(config, f, indent=2)
        print(f"\n💾 Configuration saved to {filename}")

    def run(self):
        """Run full optimization analysis"""
        print("="*60)
        print("STRATEGY OPTIMIZATION")
        print("="*60)

        results = self.get_evaluated_results()

        if not results:
            print("\nNo settled trades to analyze yet")
            return

        print(f"\nAnalyzing {len(results)} settled trades...")

        config = self.generate_config_suggestions(results)

        if config:
            self.save_optimized_config(config)


if __name__ == "__main__":
    optimizer = StrategyOptimizer()
    optimizer.run()
