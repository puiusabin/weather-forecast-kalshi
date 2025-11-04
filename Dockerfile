FROM python:3.12-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    cron \
    procps \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application files
COPY data_fetchers.py .
COPY data_logger.py .
COPY live_trader.py .
COPY live_trader_enhanced.py .
COPY additional_sources.py .
COPY track_performance.py .
COPY analyze_sources.py .
COPY automated_runner.py .

# Create data directory for persistent storage
RUN mkdir -p /app/data

# Copy crontab file
COPY crontab /etc/cron.d/trading-cron

# Give execution rights on the cron job
RUN chmod 0644 /etc/cron.d/trading-cron

# Apply cron job
RUN crontab /etc/cron.d/trading-cron

# Create log file
RUN touch /var/log/cron.log

# Run the command on container startup
CMD cron && tail -f /var/log/cron.log
