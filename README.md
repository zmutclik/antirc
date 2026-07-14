# AntiRC - IRC Bot for Linux Server Management

AntiRC adalah solusi monitoring dan otomasi update untuk server/container Linux berbasis IRC. Bot Python berjalan di setiap server, terhubung ke private IRC server, dengan The Lounge sebagai web admin interface.

## Arsitektur

```
Admin Browser (The Lounge) <-> Private IRC Server (InspIRCd) <-> Python IRC Bot (per server)
```

## Fitur

- **Monitoring Real-time**: CPU, RAM, disk, network, services, Docker containers
- **Security Alerts**: Failed SSH, sudo failures dari auth.log
- **Auto Update**: Scheduled apt update/upgrade dengan laporan ke IRC
- **Web Admin**: The Lounge sebagai IRC client berbasis browser
- **Multi-Server**: Deploy ke banyak server dengan Ansible
- **Autentikasi**: Nick-based + hostmask verification

## Quick Start

### 1. Deploy IRC Server + The Lounge (Docker)

```bash
cd antirc
docker-compose up -d ircd thelounge
```

Akses The Lounge di `http://localhost:9000`

### 2. Install Bot di Server

```bash
# Via install script
curl -sL http://zmutclik.my.id/download/antirc.sh | sudo bash

# Atau manual
git clone https://github.com/zmutclik/antirc.git /opt/antircbot
cd /opt/antircbot
pip install -r requirements.txt
cp config.ini.example /etc/antircbot/config.ini
# Edit /etc/antircbot/config.ini
sudo systemctl start ircbot
```

### 3. Ansible Deploy (Multi-Server)

```bash
cd deploy/ansible
ansible-playbook -i inventory.yml playbook.yml \
  -e "antirc_irc_host=irc.local" \
  -e "antirc_admins=admin1,admin2"
```

## Commands

| Command | Deskripsi | Akses |
|---------|-----------|-------|
| `!status` | CPU, RAM, load, uptime | Public |
| `!disk` | Disk usage per mount | Public |
| `!services [name]` | Systemd service status | Public |
| `!net` | Network interfaces & stats | Public |
| `!docker` | Docker container list | Public |
| `!logs [service] [lines]` | Tail journalctl | Public |
| `!alerts` | Security alerts | Public |
| `!update` | Check apt updates | Admin |
| `!upgrade --force` | Run apt upgrade | Admin |
| `!autoupdate [on\|off]` | Toggle auto-update cron | Admin |
| `!auth <password>` | Authenticate as admin | Admin |
| `!addadmin <nick>` | Add admin | Admin |
| `!deladmin <nick>` | Remove admin | Admin |
| `!help` | Show help | Public |

## Konfigurasi

Edit `config.ini` atau gunakan environment variables:

```bash
export ANTIRC_IRC_HOST=irc.local
export ANTIRC_IRC_PORT=6667
export ANTIRC_IRC_CHANNEL=#sysadmin
export ANTIRC_AUTH_ADMINS=admin1,admin2
export ANTIRC_BOT_AUTO_REPORT_INTERVAL=300
```

## Docker

```bash
docker build -f docker/Dockerfile -t antircbot .
docker run -d \
  -e ANTIRC_IRC_HOST=irc.local \
  -v /var/run/docker.sock:/var/run/docker.sock:ro \
  -v ./config.ini:/etc/antircbot/config.ini:ro \
  antircbot
```

## mIRC Admin Script (Opsional)

Untuk admin yang menggunakan Windows + mIRC:

1. Copy `admin/mirc-admin.mrc` ke mIRC Remotes (Alt+R)
2. Tekan F5 untuk refresh status
3. Gunakan popup menu di channel untuk commands

## Keamanan

- Bot berjalan sebagai user `antircbot` (non-root)
- Sudo NOPASSWD hanya untuk apt commands
- Autentikasi nick + hostmask
- Password opsional untuk operasi berbahaya
- Channel key dan SSL/TLS support

## Troubleshooting

```bash
# Check bot status
systemctl status ircbot
journalctl -u ircbot -f

# Check logs
tail -f /var/log/antircbot.log
tail -f /var/log/antircbot-auto-update.log

# Test IRC connection
nc -v irc.local 6667
```

## License

MIT License
