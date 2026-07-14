#!/bin/bash
# AntiRC Bot Installation Script
# Usage: curl -sL https://your-server/install.sh | bash
# Or: wget -qO- https://your-server/install.sh | bash

set -e

REPO_URL="https://github.com/yourusername/antirc.git"
INSTALL_DIR="/opt/antircbot"
CONFIG_DIR="/etc/antircbot"
LOG_DIR="/var/log"
USER="antircbot"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo -e "${GREEN}=== AntiRC Bot Installer ===${NC}"

# Check root
if [ "$EUID" -ne 0 ]; then
    echo -e "${RED}Please run as root (use sudo)${NC}"
    exit 1
fi

# Detect OS
if [ -f /etc/debian_version ]; then
    echo -e "${GREEN}Detected Debian/Ubuntu${NC}"
    apt-get update -qq
    apt-get install -y -qq python3 python3-pip python3-venv git curl netcat-openbsd
elif [ -f /etc/redhat-release ]; then
    echo -e "${GREEN}Detected RHEL/CentOS${NC}"
    yum install -y -q python3 python3-pip git curl nc
else
    echo -e "${YELLOW}Unknown OS, please install python3, pip, git, curl, nc manually${NC}"
fi

# Create user
if ! id "$USER" &>/dev/null; then
    useradd -r -s /bin/false -d "$INSTALL_DIR" "$USER"
    echo -e "${GREEN}Created user: $USER${NC}"
fi

# Install bot
if [ -d "$INSTALL_DIR" ]; then
    echo -e "${YELLOW}Updating existing installation...${NC}"
    cd "$INSTALL_DIR"
    git pull || true
else
    echo -e "${GREEN}Cloning repository...${NC}"
    git clone "$REPO_URL" "$INSTALL_DIR" || {
        echo -e "${YELLOW}Git clone failed, copying local files...${NC}"
        mkdir -p "$INSTALL_DIR"
        cp -r "$(dirname "$0")/.."/* "$INSTALL_DIR/"
    }
fi

# Setup Python venv
cd "$INSTALL_DIR"
python3 -m venv venv
source venv/bin/activate
pip install -q -r requirements.txt

# Create config directory
mkdir -p "$CONFIG_DIR"

# Create default config if not exists
if [ ! -f "$CONFIG_DIR/config.ini" ]; then
    cat > "$CONFIG_DIR/config.ini" << 'EOF'
[irc]
host = irc.local
port = 6667
tls = false
nick = antircbot
realname = AntiRC System Bot
channel = #sysadmin
channel_key =

[auth]
admins =
require_password = false
admin_password = changeme

[bot]
auto_report_interval = 300
log_file = /var/log/antircbot.log
data_dir = /var/lib/antircbot
EOF
    echo -e "${YELLOW}Created default config at $CONFIG_DIR/config.ini${NC}"
    echo -e "${YELLOW}Please edit it with your IRC server details and admin nicks!${NC}"
fi

# Create data and log directories
mkdir -p /var/lib/antircbot
mkdir -p "$LOG_DIR"
touch "$LOG_DIR/antircbot.log"
touch "$LOG_DIR/antircbot-auto-update.log"
chown -R "$USER:$USER" "$INSTALL_DIR" /var/lib/antircbot
chown "$USER:$USER" "$LOG_DIR"/antircbot*.log

# Install systemd service
cp "$INSTALL_DIR/systemd/ircbot.service" /etc/systemd/system/
sed -i "s|/opt/antircbot|$INSTALL_DIR|g" /etc/systemd/system/ircbot.service
systemctl daemon-reload
systemctl enable ircbot

# Create symlink for easy access
ln -sf "$INSTALL_DIR/bot/ircbot.py" /usr/local/bin/antircbot

# Setup sudo for apt (optional but recommended)
if [ -d /etc/sudoers.d ]; then
    cat > /etc/sudoers.d/antircbot << EOF
$USER ALL=(ALL) NOPASSWD: /usr/bin/apt update, /usr/bin/apt upgrade *, /usr/bin/apt autoremove *, /usr/bin/apt list --upgradable
EOF
    chmod 440 /etc/sudoers.d/antircbot
    echo -e "${GREEN}Configured sudo for apt commands${NC}"
fi

echo -e "${GREEN}=== Installation Complete ===${NC}"
echo -e "Config: ${YELLOW}$CONFIG_DIR/config.ini${NC}"
echo -e "Start:  ${YELLOW}systemctl start ircbot${NC}"
echo -e "Status: ${YELLOW}systemctl status ircbot${NC}"
echo -e "Logs:   ${YELLOW}journalctl -u ircbot -f${NC}"
echo ""
echo -e "${YELLOW}IMPORTANT: Edit $CONFIG_DIR/config.ini before starting!${NC}"
