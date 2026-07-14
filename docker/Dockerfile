# AntiRC Bot Docker Image
FROM python:3.11-slim

LABEL maintainer="antirc"
LABEL description="AntiRC IRC Bot for Linux monitoring and update automation"

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    netcat-openbsd \
    sudo \
    systemd \
    && rm -rf /var/lib/apt/lists/*

# Create user
RUN useradd -r -s /bin/false -m antircbot && \
    usermod -aG sudo antircbot

# Setup sudo for apt
RUN echo "antircbot ALL=(ALL) NOPASSWD: /usr/bin/apt update, /usr/bin/apt upgrade *, /usr/bin/apt autoremove *, /usr/bin/apt list --upgradable" > /etc/sudoers.d/antircbot && \
    chmod 440 /etc/sudoers.d/antircbot

# Set working directory
WORKDIR /opt/antircbot

# Copy requirements first for better caching
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy bot code
COPY bot/ ./bot/
COPY cron/ ./cron/

# Create directories
RUN mkdir -p /var/lib/antircbot /var/log /etc/antircbot && \
    chown -R antircbot:antircbot /opt/antircbot /var/lib/antircbot /var/log

# Copy default config
COPY config.ini.example /etc/antircbot/config.ini

# Environment
ENV ANTIRC_CONFIG=/etc/antircbot/config.ini
ENV PYTHONUNBUFFERED=1

# Switch to non-root user
USER antircbot

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD pgrep -f ircbot.py || exit 1

# Run bot
CMD ["python", "bot/ircbot.py"]
