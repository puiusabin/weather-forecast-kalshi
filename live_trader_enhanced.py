"""
Enhanced live trader with MSN Weather and additional sources
Based on user feedback that MSN has best data
"""
import requests
from datetime import datetime
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass
import json
from live_trader import WeatherForecasts, LiveTrader, TradingDecision


class EnhancedWeatherForecasts(WeatherForecasts):
    """Extended weather forecasts including MSN and others"""

    @staticmethod
    def get_msn_forecast(target_date: datetime) -> Optional[float]:
        """
        Get MSN Weather forecast - reportedly most accurate based on user research
        MSN aggregates multiple sources
        """
        try:
            # Try to get data from MSN Weather API endpoint
            # MSN doesn't have a public API, but we can try their data endpoint
            url = "https://www.msn.com/en-us/weather/forecast/in-New-York,NY"

            headers = {
                'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
            }

            response = requests.get(url, headers=headers, timeout=15)

            # Note: This is a simplified scraping approach
            # In production, you might need to handle MSN's data format more carefully
            # Consider using Selenium for JavaScript-rendered content

            if response.status_code == 200:
                # Try to extract temperature from page
                # MSN uses JSON-LD structured data sometimes
                import re
                text = response.text

                # Look for temperature patterns in the HTML
                # This is fragile and may break if MSN changes their format
                temp_patterns = [
                    r'"temperature[Mm]ax[Ff]"[:\s]+(\d+)',
                    r'"[Hh]igh[Tt]emp"[:\s]+(\d+)',
                    r'high["\s:]+(\d+)',
                ]

                for pattern in temp_patterns:
                    match = re.search(pattern, text)
                    if match:
                        return float(match.group(1))

        except Exception as e:
            print(f"MSN Weather fetch error: {e}")

        return None

    @staticmethod
    def get_weatherapi_forecast(target_date: datetime, api_key: Optional[str] = None) -> Optional[float]:
        """
        WeatherAPI.com - free tier with good coverage
        """
        if not api_key:
            return None

        try:
            url = "http://api.weatherapi.com/v1/forecast.json"
            params = {
                'key': api_key,
                'q': '40.7128,-74.0060',
                'days': 1
            }

            response = requests.get(url, params=params, timeout=10)
            if response.status_code == 200:
                data = response.json()
                return data['forecast']['forecastday'][0]['day']['maxtemp_f']

        except Exception as e:
            print(f"WeatherAPI.com error: {e}")

        return None


class EnhancedLiveTrader(LiveTrader):
    """Enhanced trader with additional forecast sources"""

    def get_today_forecast(
        self,
        openweathermap_key: Optional[str] = None,
        weatherapi_key: Optional[str] = None,
        aeris_api_id: Optional[str] = None,
        aeris_api_secret: Optional[str] = None,
        include_msn: bool = True,
        include_foreca: bool = True,
        include_weather_channel: bool = True
    ) -> Dict[str, float]:
        """Get forecasts including MSN and other sources"""
        today = datetime.now()
        forecasts = {}

        # Open-Meteo (free, reliable)
        temp = WeatherForecasts.get_openmeteo_forecast(today)
        if temp:
            forecasts['OpenMeteo'] = temp

        # NWS (free, official US)
        temp = WeatherForecasts.get_nws_forecast(today)
        if temp:
            forecasts['NWS'] = temp

        # Priority sources from user research for NYC
        from additional_sources import AdditionalWeatherSources

        # Foreca (user research: good for NYC)
        if include_foreca:
            temp = AdditionalWeatherSources.get_foreca()
            if temp:
                forecasts['Foreca'] = temp
                print("✓ Foreca data retrieved (user research: good for NYC)")

        # AerisWeather (user research: good for NYC, requires API)
        if aeris_api_id and aeris_api_secret:
            temp = AdditionalWeatherSources.get_aerisweather(aeris_api_id, aeris_api_secret)
            if temp:
                forecasts['AerisWeather'] = temp
                print("✓ AerisWeather data retrieved (user research: good for NYC)")

        # The Weather Channel (user research: good for NYC)
        if include_weather_channel:
            temp = AdditionalWeatherSources.get_weather_channel()
            if temp:
                forecasts['WeatherChannel'] = temp
                print("✓ Weather Channel data retrieved (user research: good for NYC)")

        # MSN Weather (previous research: good results)
        if include_msn:
            temp = EnhancedWeatherForecasts.get_msn_forecast(today)
            if temp:
                forecasts['MSN'] = temp
                print("✓ MSN Weather data retrieved")

        # OpenWeatherMap (optional)
        if openweathermap_key:
            temp = WeatherForecasts.get_openweathermap_forecast(today, openweathermap_key)
            if temp:
                forecasts['OpenWeatherMap'] = temp

        # WeatherAPI.com (optional)
        if weatherapi_key:
            temp = EnhancedWeatherForecasts.get_weatherapi_forecast(today, weatherapi_key)
            if temp:
                forecasts['WeatherAPI'] = temp

        return forecasts

    def get_weighted_consensus(self, forecasts: Dict[str, float]) -> Tuple[float, float]:
        """
        Get weighted consensus with higher weight for MSN (based on user research)
        """
        if not forecasts:
            return None, 0.0

        # Assign weights based on user research and observed accuracy
        weights = {
            # User research: best for NYC
            'Foreca': 2.0,         # User research: good for NYC
            'AerisWeather': 2.0,   # User research: good for NYC
            'WeatherChannel': 2.0, # User research: good for NYC
            'MSN': 2.0,            # Previous research: good results

            # Standard sources
            'NWS': 1.5,            # Official US government
            'OpenMeteo': 1.0,      # Good baseline
            'OpenWeatherMap': 1.0,
            'WeatherAPI': 1.0,
        }

        # Calculate weighted average
        weighted_sum = 0.0
        total_weight = 0.0

        for source, temp in forecasts.items():
            weight = weights.get(source, 1.0)
            weighted_sum += temp * weight
            total_weight += weight

        consensus = weighted_sum / total_weight if total_weight > 0 else 0

        # Calculate confidence
        # Higher confidence if any priority source agrees with consensus
        priority_sources = ['Foreca', 'AerisWeather', 'WeatherChannel', 'MSN']
        priority_agreement = False

        for source in priority_sources:
            if source in forecasts:
                diff = abs(forecasts[source] - consensus)
                if diff < 1.0:
                    priority_agreement = True
                    break

        base_confidence = 0.85 if priority_agreement else 0.70

        # Adjust confidence based on source agreement
        if len(forecasts) > 1:
            temps = list(forecasts.values())
            variance = sum((t - consensus) ** 2 for t in temps) / len(temps)
            std_dev = variance ** 0.5

            # Lower confidence if sources disagree
            confidence_penalty = min(std_dev / 3.0, 0.3)
            confidence = max(0.0, base_confidence - confidence_penalty)
        else:
            confidence = base_confidence * 0.8  # Lower if only one source

        return consensus, confidence

    def make_trading_decision(
        self,
        openweathermap_key: Optional[str] = None,
        weatherapi_key: Optional[str] = None,
        aeris_api_id: Optional[str] = None,
        aeris_api_secret: Optional[str] = None
    ) -> Optional[TradingDecision]:
        """Make enhanced trading decision"""

        # Get forecasts
        forecasts = self.get_today_forecast(
            openweathermap_key=openweathermap_key,
            weatherapi_key=weatherapi_key,
            aeris_api_id=aeris_api_id,
            aeris_api_secret=aeris_api_secret
        )

        if not forecasts:
            print("No forecasts available")
            return None

        print(f"\nForecasts for {datetime.now().date()}:")
        for source, temp in forecasts.items():
            prefix = "⭐" if source == "MSN" else "  "
            print(f"{prefix} {source}: {temp:.1f}°F")

        # Get weighted consensus (MSN has higher weight)
        consensus, confidence = self.get_weighted_consensus(forecasts)
        print(f"\nWeighted Consensus: {consensus:.1f}°F (confidence: {confidence:.1%})")

        # Get markets
        markets = self.get_todays_markets()

        if not markets:
            print("No markets available for today")
            return None

        print(f"\nAvailable markets: {len(markets)}")

        # Find best market
        best_market = self.find_best_market(markets, consensus)

        if not best_market:
            print("Could not find matching market")
            return None

        decision = TradingDecision(
            date=datetime.now().strftime('%Y-%m-%d'),
            forecast_temp=consensus,
            source="WeightedConsensus(MSN)",
            market_ticker=best_market['ticker'],
            market_subtitle=best_market['subtitle'],
            confidence=confidence
        )

        print(f"\n{'='*60}")
        print(f"TRADING DECISION:")
        print(f"  Market: {best_market['subtitle']}")
        print(f"  Ticker: {best_market['ticker']}")
        print(f"  Confidence: {confidence:.1%}")
        print(f"{'='*60}\n")

        return decision


def main():
    """Run enhanced trading system"""
    print("="*60)
    print("ENHANCED WEATHER TRADING SYSTEM")
    print("(Includes MSN Weather - User's Preferred Source)")
    print("="*60)

    trader = EnhancedLiveTrader()

    # Make decision
    decision = trader.make_trading_decision()

    if decision:
        # Log the trade
        trader.log_trade(decision)

        print("\nNext steps:")
        print(f"1. Go to Kalshi and find market: {decision.market_ticker}")
        print(f"2. Buy 'Yes' on: {decision.market_subtitle}")
        print(f"3. Best entry time: 9 AM your time (40-50¢ typical price)")
        print(f"4. Settlement: https://forecast.weather.gov/product.php?site=OKX&product=CLI&issuedby=NYC")


if __name__ == "__main__":
    main()
