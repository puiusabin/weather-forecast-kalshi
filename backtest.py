"""
Backtesting engine for weather forecast trading strategies
"""
from datetime import datetime, timedelta
from typing import List, Dict, Optional
from dataclasses import dataclass, field
from data_fetchers import (
    OpenMeteoFetcher,
    KalshiFetcher,
    ForecastTemp,
    KalshiMarket
)


@dataclass
class Trade:
    """Represents a single trade"""
    date: str
    forecast_temp: float
    actual_temp: float
    predicted_market: Optional[str]  # Subtitle of market we bet on
    winning_market: Optional[str]    # Subtitle of actual winner
    won: bool
    forecast_source: str


@dataclass
class StrategyResult:
    """Results for a single strategy"""
    strategy_name: str
    trades: List[Trade] = field(default_factory=list)
    total_trades: int = 0
    wins: int = 0
    losses: int = 0
    win_rate: float = 0.0
    avg_forecast_error: float = 0.0

    def calculate_stats(self):
        """Calculate summary statistics"""
        self.total_trades = len(self.trades)
        self.wins = sum(1 for t in self.trades if t.won)
        self.losses = self.total_trades - self.wins
        self.win_rate = self.wins / self.total_trades if self.total_trades > 0 else 0

        errors = [abs(t.forecast_temp - t.actual_temp) for t in self.trades]
        self.avg_forecast_error = sum(errors) / len(errors) if errors else 0

    def __str__(self):
        return (
            f"\n{'='*60}\n"
            f"Strategy: {self.strategy_name}\n"
            f"{'='*60}\n"
            f"Total Trades: {self.total_trades}\n"
            f"Wins: {self.wins}\n"
            f"Losses: {self.losses}\n"
            f"Win Rate: {self.win_rate:.1%}\n"
            f"Avg Forecast Error: {self.avg_forecast_error:.2f}°F\n"
            f"{'='*60}"
        )


class ForecastStrategy:
    """Base class for forecast strategies"""

    def __init__(self, name: str):
        self.name = name

    def get_forecast(self, forecast_date: datetime, target_date: datetime) -> Optional[float]:
        """Get temperature forecast. Override in subclasses."""
        raise NotImplementedError


class SameDayForecast(ForecastStrategy):
    """Use forecast made on the same day (morning forecast for that day)"""

    def __init__(self):
        super().__init__("Same-Day Morning Forecast")

    def get_forecast(self, forecast_date: datetime, target_date: datetime) -> Optional[float]:
        """Get forecast made on target_date for target_date"""
        forecast = OpenMeteoFetcher.get_historical_forecast(target_date, target_date)
        return forecast.temp_f if forecast else None


class OneDayAheadForecast(ForecastStrategy):
    """Use forecast made 1 day before"""

    def __init__(self):
        super().__init__("1-Day Ahead Forecast")

    def get_forecast(self, forecast_date: datetime, target_date: datetime) -> Optional[float]:
        """Get forecast made 1 day before target_date"""
        forecast_date = target_date - timedelta(days=1)
        forecast = OpenMeteoFetcher.get_historical_forecast(forecast_date, target_date)
        return forecast.temp_f if forecast else None


class TwoDayAheadForecast(ForecastStrategy):
    """Use forecast made 2 days before"""

    def __init__(self):
        super().__init__("2-Day Ahead Forecast")

    def get_forecast(self, forecast_date: datetime, target_date: datetime) -> Optional[float]:
        """Get forecast made 2 days before target_date"""
        forecast_date = target_date - timedelta(days=2)
        forecast = OpenMeteoFetcher.get_historical_forecast(forecast_date, target_date)
        return forecast.temp_f if forecast else None


class WeightedAverageForecast(ForecastStrategy):
    """Use weighted average of multiple forecasts"""

    def __init__(self):
        super().__init__("Weighted Average (3-day window)")

    def get_forecast(self, forecast_date: datetime, target_date: datetime) -> Optional[float]:
        """Get weighted average of forecasts from 0-2 days before"""
        forecasts = []

        for days_before in range(3):
            f_date = target_date - timedelta(days=days_before)
            forecast = OpenMeteoFetcher.get_historical_forecast(f_date, target_date)
            if forecast:
                # Weight more recent forecasts higher
                weight = 3 - days_before  # 3, 2, 1
                forecasts.append((forecast.temp_f, weight))

        if not forecasts:
            return None

        weighted_sum = sum(temp * weight for temp, weight in forecasts)
        total_weight = sum(weight for _, weight in forecasts)

        return weighted_sum / total_weight


class Backtester:
    """Backtest forecast strategies"""

    def __init__(self, start_date: datetime, end_date: datetime):
        self.start_date = start_date
        self.end_date = end_date

    def test_strategy(self, strategy: ForecastStrategy) -> StrategyResult:
        """Test a single strategy over the date range"""
        result = StrategyResult(strategy_name=strategy.name)

        current_date = self.start_date
        while current_date <= self.end_date:
            # Get markets for this date
            markets = KalshiFetcher.get_markets_for_date(current_date)

            if not markets:
                print(f"⚠ No markets found for {current_date.date()}")
                current_date += timedelta(days=1)
                continue

            # Get forecast
            forecast_temp = strategy.get_forecast(current_date, current_date)

            if forecast_temp is None:
                print(f"⚠ No forecast available for {current_date.date()}")
                current_date += timedelta(days=1)
                continue

            # Get actual temperature
            actual_temp = OpenMeteoFetcher.get_actual_temp(current_date)

            if actual_temp is None:
                print(f"⚠ No actual temp for {current_date.date()}")
                current_date += timedelta(days=1)
                continue

            # Find markets
            predicted_market = KalshiFetcher.find_market_for_forecast(markets, forecast_temp)
            winning_market = KalshiFetcher.find_winning_market(markets, actual_temp)

            if not predicted_market or not winning_market:
                print(f"⚠ Could not match markets for {current_date.date()}")
                current_date += timedelta(days=1)
                continue

            # Record trade
            won = predicted_market.subtitle == winning_market.subtitle
            trade = Trade(
                date=current_date.strftime('%Y-%m-%d'),
                forecast_temp=forecast_temp,
                actual_temp=actual_temp,
                predicted_market=predicted_market.subtitle,
                winning_market=winning_market.subtitle,
                won=won,
                forecast_source=strategy.name
            )

            result.trades.append(trade)

            status = "✓ WIN " if won else "✗ LOSS"
            print(f"{current_date.date()}: {status} | Forecast: {forecast_temp:.1f}°F ({predicted_market.subtitle}) | Actual: {actual_temp:.1f}°F ({winning_market.subtitle})")

            current_date += timedelta(days=1)

        result.calculate_stats()
        return result

    def compare_strategies(self, strategies: List[ForecastStrategy]) -> Dict[str, StrategyResult]:
        """Test multiple strategies and compare results"""
        results = {}

        for strategy in strategies:
            print(f"\n{'='*60}")
            print(f"Testing Strategy: {strategy.name}")
            print(f"{'='*60}\n")

            result = self.test_strategy(strategy)
            results[strategy.name] = result

        return results


def main():
    """Run backtest for past 30 days"""
    end_date = datetime.now() - timedelta(days=1)  # Yesterday
    start_date = end_date - timedelta(days=30)  # 30 days ago

    print(f"Backtesting from {start_date.date()} to {end_date.date()}\n")

    # Define strategies to test
    strategies = [
        SameDayForecast(),
        OneDayAheadForecast(),
        TwoDayAheadForecast(),
        WeightedAverageForecast(),
    ]

    # Run backtest
    backtester = Backtester(start_date, end_date)
    results = backtester.compare_strategies(strategies)

    # Print results
    print("\n\n" + "="*60)
    print("FINAL RESULTS")
    print("="*60)

    # Sort by win rate
    sorted_results = sorted(results.values(), key=lambda x: x.win_rate, reverse=True)

    for i, result in enumerate(sorted_results, 1):
        print(f"\n#{i} {result}")

    # Find best strategy
    best = sorted_results[0]
    print(f"\n{'='*60}")
    print(f"🏆 BEST STRATEGY: {best.strategy_name}")
    print(f"   Win Rate: {best.win_rate:.1%} ({best.wins}/{best.total_trades})")
    print(f"   Avg Error: {best.avg_forecast_error:.2f}°F")
    print(f"{'='*60}\n")


if __name__ == "__main__":
    main()
