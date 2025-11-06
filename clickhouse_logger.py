"""
ClickHouse Logger - Push all monitoring data to analytics DB

Handles:
- Temperature observations (every 5 min)
- Monitoring sessions
- Daily trading results
- Source accuracy
- Market analysis
"""
import requests
import json
import os
from datetime import datetime
from typing import Dict, List, Optional
from dataclasses import dataclass


class ClickHouseLogger:
    """Log data to ClickHouse for analytics"""

    def __init__(
        self,
        host: str = "localhost",
        port: int = 8123,
        database: str = "weather_analytics"
    ):
        self.host = host
        self.port = port
        self.database = database
        self.base_url = f"http://{host}:{port}"

    def execute_query(self, query: str) -> Optional[Dict]:
        """Execute a query against ClickHouse"""
        try:
            url = f"{self.base_url}/"
            params = {
                'database': self.database,
                'query': query
            }

            response = requests.post(url, params=params, timeout=10)
            if response.status_code == 200:
                return response.text
            else:
                print(f"ClickHouse query error: {response.status_code} - {response.text}")
                return None

        except Exception as e:
            print(f"ClickHouse connection error: {e}")
            return None

    def insert_temperature_observation(
        self,
        timestamp: datetime,
        source: str,
        temperature: float,
        is_forecast: bool,
        session_id: str
    ):
        """Insert a single temperature observation"""
        query = f"""
        INSERT INTO temperature_observations
        (timestamp, date, hour, minute, source, temperature, is_forecast, session_id)
        VALUES (
            '{timestamp.strftime('%Y-%m-%d %H:%M:%S')}',
            '{timestamp.strftime('%Y-%m-%d')}',
            {timestamp.hour},
            {timestamp.minute},
            '{source}',
            {temperature},
            {1 if is_forecast else 0},
            '{session_id}'
        )
        """

        return self.execute_query(query)

    def insert_monitoring_session(self, session_data: Dict):
        """Insert a complete monitoring session"""
        query = f"""
        INSERT INTO monitoring_sessions
        (session_id, date, start_time, end_time, predicted_max_hour,
         predicted_max_temp, detected_max_temp, detected_max_time,
         confidence, bet_decision, observations_count, duration_minutes)
        VALUES (
            '{session_data['session_id']}',
            '{session_data['date']}',
            '{session_data['start_time']}',
            '{session_data['end_time']}',
            {session_data['predicted_max_hour']},
            {session_data['predicted_max_temp']},
            {session_data['detected_max_temp']},
            '{session_data['detected_max_time']}',
            {session_data['confidence']},
            '{session_data['bet_decision']}',
            {session_data['observations_count']},
            {session_data['duration_minutes']}
        )
        """

        # First insert session
        result = self.execute_query(query)

        # Then insert all observations
        if 'observations' in session_data:
            for obs in session_data['observations']:
                obs_time = datetime.strptime(obs['timestamp'], '%Y-%m-%d %H:%M:%S')
                self.insert_temperature_observation(
                    timestamp=obs_time,
                    source=obs['source'],
                    temperature=obs['temperature'],
                    is_forecast=obs['is_forecast'],
                    session_id=session_data['session_id']
                )

        return result

    def insert_daily_result(self, result_data: Dict):
        """Insert daily trading result"""
        sources = ','.join(result_data.get('sources_used', []))

        query = f"""
        INSERT INTO daily_results
        (date, strategy, forecast_consensus, forecast_confidence,
         observed_max, actual_max, predicted_correct, trade_placed,
         trade_won, market_ticker, market_subtitle, error_magnitude,
         sources_used, num_sources)
        VALUES (
            '{result_data['date']}',
            '{result_data['strategy']}',
            {result_data.get('forecast_consensus', 0)},
            {result_data.get('forecast_confidence', 0)},
            {result_data.get('observed_max', 0)},
            {result_data.get('actual_max', 0)},
            {1 if result_data.get('predicted_correct', False) else 0},
            {1 if result_data.get('trade_placed', False) else 0},
            {1 if result_data.get('trade_won', False) else 0},
            '{result_data.get('market_ticker', '')}',
            '{result_data.get('market_subtitle', '')}',
            {result_data.get('error_magnitude', 0)},
            ['{sources}'],
            {result_data.get('num_sources', 0)}
        )
        """

        return self.execute_query(query)

    def insert_source_accuracy(
        self,
        date: str,
        source: str,
        forecast_temp: float,
        actual_temp: float,
        was_available: bool
    ):
        """Track individual source accuracy"""
        error = abs(forecast_temp - actual_temp)

        query = f"""
        INSERT INTO source_accuracy
        (date, source, forecast_temp, actual_temp, error, was_available, fetch_time)
        VALUES (
            '{date}',
            '{source}',
            {forecast_temp},
            {actual_temp},
            {error},
            {1 if was_available else 0},
            '{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}'
        )
        """

        return self.execute_query(query)

    def get_win_rate_by_strategy(self) -> Optional[List[Dict]]:
        """Query win rates by strategy"""
        query = "SELECT * FROM win_rate_by_strategy"
        result = self.execute_query(query)

        if result:
            # Parse TSV response from ClickHouse
            lines = result.strip().split('\n')
            if len(lines) > 0:
                # Parse as JSON-like (ClickHouse can output JSON format)
                return result

        return None

    def get_source_rankings(self) -> Optional[str]:
        """Get source accuracy rankings"""
        query = "SELECT * FROM source_rankings FORMAT Pretty"
        return self.execute_query(query)

    def get_recent_sessions(self, days: int = 7) -> Optional[str]:
        """Get recent monitoring sessions"""
        query = f"""
        SELECT
            date,
            predicted_max_hour,
            predicted_max_temp,
            detected_max_temp,
            confidence,
            bet_decision,
            CASE
                WHEN bet_won = 1 THEN 'WIN'
                WHEN bet_won = 0 THEN 'LOSS'
                ELSE 'PENDING'
            END as outcome
        FROM monitoring_sessions
        WHERE date >= today() - INTERVAL {days} DAY
        ORDER BY date DESC
        FORMAT Pretty
        """
        return self.execute_query(query)


def import_json_session_to_clickhouse(json_file: str):
    """Import a monitoring session JSON file to ClickHouse"""
    logger = ClickHouseLogger(
        host=os.environ.get('CLICKHOUSE_HOST', 'localhost'),
        port=int(os.environ.get('CLICKHOUSE_PORT', 8123))
    )

    with open(json_file, 'r') as f:
        session_data = json.load(f)

    # Add session ID
    session_data['session_id'] = f"session_{session_data['date']}_{session_data['start_time']}"

    # Calculate duration
    start = datetime.strptime(session_data['start_time'], '%Y-%m-%d %H:%M:%S')
    end = datetime.strptime(session_data['end_time'], '%Y-%m-%d %H:%M:%S')
    session_data['duration_minutes'] = int((end - start).total_seconds() / 60)
    session_data['observations_count'] = len(session_data['observations'])

    # Insert to ClickHouse
    logger.insert_monitoring_session(session_data)
    print(f"✓ Imported {json_file} to ClickHouse")


def test_clickhouse_connection():
    """Test connection to ClickHouse"""
    logger = ClickHouseLogger()

    print("Testing ClickHouse connection...")
    result = logger.execute_query("SELECT 1")

    if result:
        print("✓ ClickHouse connected successfully!")
        print(f"Response: {result}")

        # Test query
        print("\nQuerying source rankings...")
        rankings = logger.get_source_rankings()
        if rankings:
            print(rankings)
    else:
        print("✗ Could not connect to ClickHouse")


if __name__ == "__main__":
    test_clickhouse_connection()
