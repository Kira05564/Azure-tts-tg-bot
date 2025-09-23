# Base image
FROM python:3.9-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && \
    apt-get install -y ffmpeg git && \
    rm -rf /var/lib/apt/lists/*

# Copy requirements and install
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy bot code
COPY bot.py .

# Set environment variable for Telegram Bot Token
ENV BOT_TOKEN="7730705217:AAHCQmZ7f47Y7a4q2XA15FJJEwpKCbMo1eQ"

# Start bot
CMD ["python", "bot.py"]