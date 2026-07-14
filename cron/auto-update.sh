#!/bin/bash
# AntiRC Auto-Update Script
# Runs apt update + upgrade and reports to IRC channel via bot

LOG_FILE="/var/log/antircbot-auto-update.log"
HOSTNAME=$(hostname)
IRC_HOST="${ANTIRC_IRC_HOST:-irc.local}"
IRC_PORT="${ANTIRC_IRC_PORT:-6667}"
IRC_CHANNEL="${ANTIRC_IRC_CHANNEL:-#sysadmin}"
IRC_NICK="${ANTIRC_IRC_NICK:-antircbot}"

echo "[$(date)] Starting auto-update on ${HOSTNAME}" >> "$LOG_FILE"

# Update package lists
apt update >> "$LOG_FILE" 2>&1
UPDATE_EXIT=$?

if [ $UPDATE_EXIT -ne 0 ]; then
    echo "[$(date)] apt update failed" >> "$LOG_FILE"
    # Try to notify via IRC (simple netcat)
    {
        echo "NICK ${IRC_NICK}-auto"
        echo "USER ${IRC_NICK}-auto 0 * :Auto Update"
        sleep 2
        echo "JOIN ${IRC_CHANNEL}"
        sleep 1
        echo "PRIVMSG ${IRC_CHANNEL} :[${HOSTNAME}] \x034Auto-update FAILED:\x03 apt update error"
        echo "QUIT"
    } | nc -q 5 "$IRC_HOST" "$IRC_PORT" 2>/dev/null || true
    exit 1
fi

# Count upgradable packages
UPGRADABLE=$(apt list --upgradable 2>/dev/null | grep -v "Listing" | grep -v "^$" | wc -l)

if [ "$UPGRADABLE" -eq 0 ]; then
    echo "[$(date)] No packages to upgrade" >> "$LOG_FILE"
    exit 0
fi

echo "[$(date)] ${UPGRADABLE} packages to upgrade" >> "$LOG_FILE"

# Run upgrade
apt upgrade -y >> "$LOG_FILE" 2>&1
UPGRADE_EXIT=$?

# Check if reboot required
REBOOT=""
if [ -f /var/run/reboot-required ]; then
    REBOOT=" | REBOOT REQUIRED"
fi

if [ $UPGRADE_EXIT -eq 0 ]; then
    MSG="[${HOSTNAME}] Auto-update complete: ${UPGRADABLE} packages upgraded${REBOOT}"
    echo "[$(date)] Upgrade successful" >> "$LOG_FILE"
else
    MSG="[${HOSTNAME}] \x034Auto-update FAILED:\x03 apt upgrade error${REBOOT}"
    echo "[$(date)] Upgrade failed" >> "$LOG_FILE"
fi

# Notify via IRC
{
    echo "NICK ${IRC_NICK}-auto"
    echo "USER ${IRC_NICK}-auto 0 * :Auto Update"
    sleep 2
    echo "JOIN ${IRC_CHANNEL}"
    sleep 1
    echo "PRIVMSG ${IRC_CHANNEL} :${MSG}"
    echo "QUIT"
} | nc -q 5 "$IRC_HOST" "$IRC_PORT" 2>/dev/null || true

# Autoremove
apt autoremove -y >> "$LOG_FILE" 2>&1

echo "[$(date)] Auto-update finished" >> "$LOG_FILE"
