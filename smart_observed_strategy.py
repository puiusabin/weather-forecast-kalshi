"""
Smart Observed Data Strategy with Continuous Monitoring

Strategy:
1. Morning: Check forecast for predicted max time (e.g., 2 PM)
2. Buffer period: (Predicted time) to (Predicted time + 1 hour)
3. Monitor: Check NWS + OpenMeteo every 5 minutes during buffer
4. Detect: When temperature starts declining = we found the max
5. Bet: On the observed maximum temperature
6. Log: Everything for analytics

Example:
- Forecast says max at 2 PM
- Start monitoring at 2 PM
- Observations: 2:00=57°F, 2:05=57°F, 2:10=58°F, 2:15=58°F, 2:20=57°F
- Detected: Max was 58°F (temp started declining after 2:15)
- Bet: 58°F bucket
- Confidence: 95% (using observed data)
"""
import requests
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, asdict
import json
import os


@dataclass
class TemperatureObservation:
    """Single temperature observation"""
    timestamp: str
    source: str  # 'NWS' or 'OpenMeteo'
    temperature: float
    is_forecast: bool  # False for observations, True for forecasts


@dataclass
class MonitoringSession:
    """Complete monitoring session for a day"""
    date: str
    start_time: str
    end_time: str
    predicted_max_hour: int
    predicted_max_temp: float
    observations: List[TemperatureObservation]
    detected_max_temp: float
    detected_max_time: str
    confidence: float
    bet_decision: str


class ContinuousMonitor:
    """Monitor temperature continuously during buffer period"""

    NYC_LAT = 40.7831  # Central Park
    NYC_LON = -73.9712

    def __init__(self, data_dir: Optional[str] = None):
        # Use /app for Docker, ./data for local testing
        if data_dir is None:
            if os.path.exists('/app'):
                data_dir = '/app/data/monitoring'
            else:
                data_dir = './data/monitoring'

        self.data_dir = data_dir
        os.makedirs(data_dir, exist_ok=True)
        self.observations = []

    def get_nws_current_observation(self) -> Optional[float]:
        """
        Get current temperature from NWS observation station
        This is ACTUAL measured data, not forecast
        """
        try:
            lat, lon = self.NYC_LAT, self.NYC_LON

            # Get observation station
            points_url = f"https://api.weather.gov/points/{lat},{lon}"
            headers = {'User-Agent': 'Weather Trading Bot'}

            response = requests.get(points_url, headers=headers, timeout=10)
            if response.status_code != 200:
                return None

            data = response.json()
            stations_url = data['properties']['observationStations']

            stations_response = requests.get(stations_url, headers=headers, timeout=10)
            if stations_response.status_code != 200:
                return None

            stations_data = stations_response.json()
            station_url = stations_data['features'][0]['id']

            # Get latest observation
            obs_url = f"{station_url}/observations/latest"
            obs_response = requests.get(obs_url, headers=headers, timeout=10)

            if obs_response.status_code == 200:
                obs_data = obs_response.json()
                temp_celsius = obs_data['properties']['temperature']['value']

                if temp_celsius is not None:
                    temp_f = (temp_celsius * 9/5) + 32
                    return temp_f

        except Exception as e:
            print(f"Error fetching NWS observation: {e}")

        return None

    def get_openmeteo_current(self) -> Optional[float]:
        """Get current temperature from OpenMeteo"""
        try:
            url = "https://api.open-meteo.com/v1/forecast"
            params = {
                'latitude': self.NYC_LAT,
                'longitude': self.NYC_LON,
                'current': 'temperature_2m',
                'temperature_unit': 'fahrenheit',
                'timezone': 'America/New_York'
            }

            response = requests.get(url, params=params, timeout=10)
            if response.status_code == 200:
                data = response.json()
                return data['current']['temperature_2m']

        except Exception as e:
            print(f"Error fetching OpenMeteo: {e}")

        return None

    def get_forecast_max_time(self, target_date: datetime) -> Tuple[Optional[int], Optional[float]]:
        """Get predicted max temp hour from OpenMeteo"""
        try:
            url = "https://api.open-meteo.com/v1/forecast"
            params = {
                'latitude': self.NYC_LAT,
                'longitude': self.NYC_LON,
                'hourly': 'temperature_2m',
                'temperature_unit': 'fahrenheit',
                'timezone': 'America/New_York',
                'forecast_days': 2
            }

            response = requests.get(url, params=params, timeout=15)
            if response.status_code == 200:
                data = response.json()

                # Find today's temps
                target_str = target_date.strftime('%Y-%m-%d')
                day_temps = []
                day_hours = []

                for i, time_str in enumerate(data['hourly']['time']):
                    if time_str.startswith(target_str):
                        day_temps.append(data['hourly']['temperature_2m'][i])
                        hour = int(time_str[11:13])
                        day_hours.append(hour)

                if day_temps:
                    max_temp = max(day_temps)
                    max_index = day_temps.index(max_temp)
                    max_hour = day_hours[max_index]
                    return max_hour, max_temp

        except Exception as e:
            print(f"Error fetching forecast: {e}")

        return None, None

    def collect_observation(self) -> Dict[str, Optional[float]]:
        """Collect temperature from all sources"""
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

        # Get NWS observation (actual measured data)
        nws_temp = self.get_nws_current_observation()
        if nws_temp:
            obs = TemperatureObservation(
                timestamp=timestamp,
                source='NWS',
                temperature=nws_temp,
                is_forecast=False
            )
            self.observations.append(obs)
            print(f"[{timestamp}] NWS: {nws_temp:.1f}°F (observed)")

        # Get OpenMeteo (may include some forecast)
        om_temp = self.get_openmeteo_current()
        if om_temp:
            obs = TemperatureObservation(
                timestamp=timestamp,
                source='OpenMeteo',
                temperature=om_temp,
                is_forecast=False
            )
            self.observations.append(obs)
            print(f"[{timestamp}] OpenMeteo: {om_temp:.1f}°F")

        return {
            'timestamp': timestamp,
            'nws': nws_temp,
            'openmeteo': om_temp
        }

    def detect_max_temperature(self, recent_observations: List[TemperatureObservation]) -> Tuple[float, str, float]:
        """
        Detect if we've passed the maximum temperature

        Logic:
        - If last 3 observations show declining trend → max already passed
        - Take the highest of recent observations as the max
        """
        if len(recent_observations) < 3:
            return None, None, 0.5

        # Get NWS observations only (most reliable)
        nws_obs = [o for o in recent_observations if o.source == 'NWS']

        if len(nws_obs) < 3:
            # Use all observations if not enough NWS
            nws_obs = recent_observations

        # Get last 3 temps
        recent_temps = [o.temperature for o in nws_obs[-3:]]

        # Check if declining
        is_declining = (recent_temps[-1] < recent_temps[-2] and
                       recent_temps[-2] <= recent_temps[-3])

        if is_declining:
            # Find max from all recent observations
            max_obs = max(nws_obs, key=lambda o: o.temperature)
            confidence = 0.90  # High confidence - temp is declining

            print(f"\n✓ DECLINING TREND DETECTED")
            print(f"  Recent temps: {' → '.join(f'{t:.1f}°F' for t in recent_temps)}")
            print(f"  Detected max: {max_obs.temperature:.1f}°F at {max_obs.timestamp}")
            print(f"  Confidence: {confidence:.1%}")

            return max_obs.temperature, max_obs.timestamp, confidence

        return None, None, 0.5

    def monitor_buffer_period(
        self,
        predicted_max_hour: int,
        predicted_max_temp: float,
        check_interval_seconds: int = 300  # 5 minutes
    ) -> MonitoringSession:
        """
        Monitor temperature during buffer period

        Args:
            predicted_max_hour: Hour when max is predicted (e.g., 14 for 2 PM)
            predicted_max_temp: Forecasted max temperature
            check_interval_seconds: How often to check (default: 5 minutes)

        Returns:
            MonitoringSession with all observations and decision
        """
        print("="*70)
        print("STARTING CONTINUOUS TEMPERATURE MONITORING")
        print("="*70)
        print(f"Predicted max: {predicted_max_temp:.1f}°F at {predicted_max_hour}:00")
        print(f"Buffer period: {predicted_max_hour}:00 to {predicted_max_hour+1}:00")
        print(f"Check interval: {check_interval_seconds}s ({check_interval_seconds/60:.0f} minutes)")
        print()

        start_time = datetime.now()
        buffer_start = start_time.replace(hour=predicted_max_hour, minute=0, second=0)
        buffer_end = buffer_start + timedelta(hours=1)

        # If we're before the buffer, wait
        if datetime.now() < buffer_start:
            wait_seconds = (buffer_start - datetime.now()).total_seconds()
            print(f"⏳ Waiting {wait_seconds/60:.0f} minutes until buffer period starts...")
            print(f"   Buffer starts at: {buffer_start.strftime('%H:%M')}")
            # In production, this would be a scheduled job
            # For testing, we skip the wait
            return None

        # Monitor during buffer period
        detected_max = None
        detected_time = None
        confidence = 0.0

        print(f"🔍 Monitoring started at {datetime.now().strftime('%H:%M:%S')}")
        print(f"   Will check every {check_interval_seconds}s until max detected or buffer ends\n")

        check_count = 0
        while datetime.now() < buffer_end:
            check_count += 1
            print(f"--- Check #{check_count} ---")

            # Collect observation
            obs = self.collect_observation()

            # Check if we've detected the max
            if len(self.observations) >= 3:
                detected_max, detected_time, confidence = self.detect_max_temperature(
                    self.observations
                )

                if detected_max is not None:
                    print(f"\n✓ MAX TEMPERATURE DETECTED!")
                    break

            # Wait before next check
            time.sleep(check_interval_seconds)

            # Safety: max 12 checks (1 hour / 5 min)
            if check_count >= 12:
                print("\n⏱ Buffer period ended")
                break

        # If we didn't detect max, use the highest observation
        if detected_max is None:
            if self.observations:
                max_obs = max(self.observations, key=lambda o: o.temperature)
                detected_max = max_obs.temperature
                detected_time = max_obs.timestamp
                confidence = 0.75  # Lower confidence - didn't see decline
                print(f"\n⚠ No declining trend detected")
                print(f"  Using highest observed: {detected_max:.1f}°F")
            else:
                # Fallback to forecast
                detected_max = predicted_max_temp
                detected_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                confidence = 0.60
                print(f"\n⚠ No observations collected")
                print(f"  Falling back to forecast: {detected_max:.1f}°F")

        # Determine bet
        bet_bucket_low = int(detected_max)
        bet_bucket_high = bet_bucket_low + 1
        bet_decision = f"{bet_bucket_low}° to {bet_bucket_high}°"

        # Create session record
        session = MonitoringSession(
            date=datetime.now().strftime('%Y-%m-%d'),
            start_time=start_time.strftime('%Y-%m-%d %H:%M:%S'),
            end_time=datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            predicted_max_hour=predicted_max_hour,
            predicted_max_temp=predicted_max_temp,
            observations=self.observations,
            detected_max_temp=detected_max,
            detected_max_time=detected_time,
            confidence=confidence,
            bet_decision=bet_decision
        )

        # Save session
        self.save_session(session)

        print("\n" + "="*70)
        print("MONITORING SESSION COMPLETE")
        print("="*70)
        print(f"Total observations: {len(self.observations)}")
        print(f"Detected max: {detected_max:.1f}°F at {detected_time}")
        print(f"Recommended bet: {bet_decision}")
        print(f"Confidence: {confidence:.1%}")
        print("="*70)

        return session

    def save_session(self, session: MonitoringSession):
        """Save session to JSON (ready for ClickHouse import)"""
        filename = f"{self.data_dir}/monitoring_{session.date}.json"

        # Convert to dict
        session_dict = asdict(session)

        # Save
        with open(filename, 'w') as f:
            json.dump(session_dict, f, indent=2)

        print(f"\n💾 Session saved: {filename}")
        print(f"   Ready for analytics import (ClickHouse/etc)")


def test_monitoring():
    """Test the continuous monitoring system"""
    monitor = ContinuousMonitor()

    # Get today's forecast
    today = datetime.now()
    predicted_hour, predicted_temp = monitor.get_forecast_max_time(today)

    if predicted_hour is None:
        print("Could not get forecast prediction")
        return

    print(f"Today's forecast: Max {predicted_temp:.1f}°F at {predicted_hour}:00\n")

    # For testing: simulate monitoring with 30-second intervals
    # In production: use 300 seconds (5 minutes)
    session = monitor.monitor_buffer_period(
        predicted_max_hour=predicted_hour,
        predicted_max_temp=predicted_temp,
        check_interval_seconds=30  # 30 seconds for testing
    )

    if session:
        print("\n📊 Ready for Kalshi bet:")
        print(f"   Market: {session.bet_decision}")
        print(f"   Confidence: {session.confidence:.1%}")


if __name__ == "__main__":
    test_monitoring()
