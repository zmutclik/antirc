"""Configuration loader for antirc bot."""
import os
import configparser
from pathlib import Path


DEFAULTS = {
    "irc": {
        "host": "antirc.zmutclik.my.id",
        "port": "6667",
        "tls": "false",
        "nick": "antircbot",
        "realname": "AntiRC System Bot",
        "channel": "#sysadmin",
        "channel_key": "",
    },
    "auth": {
        "admins": "",
        "require_password": "false",
        "admin_password": "changeme",
    },
    "bot": {
        "auto_report_interval": "300",
        "log_file": "/var/log/antircbot.log",
        "data_dir": "/var/lib/antircbot",
    },
}


def load_config(path: str = None) -> dict:
    """Load configuration from file and environment variables.

    Priority: env vars > config file > defaults.
    """
    cfg = configparser.ConfigParser()
    cfg.read_dict(DEFAULTS)

    if path and Path(path).exists():
        cfg.read(path)
    else:
        # Try common locations
        for p in ("config.ini", "/etc/antircbot/config.ini", "~/.config/antircbot/config.ini"):
            expanded = Path(p).expanduser()
            if expanded.exists():
                cfg.read(str(expanded))
                break

    # Override with environment variables
    result = {}
    for section in cfg.sections():
        result[section] = {}
        for key in cfg.options(section):
            env_key = f"ANTIRC_{section.upper()}_{key.upper()}"
            val = os.environ.get(env_key, cfg.get(section, key))
            result[section][key] = val

    # Parse lists
    result["auth"]["admins"] = [
        a.strip()
        for a in result["auth"].get("admins", "").split(",")
        if a.strip()
    ]

    # Parse booleans
    for key in ("tls", "require_password"):
        section = "irc" if key == "tls" else "auth"
        result[section][key] = result[section][key].lower() in ("true", "1", "yes", "on")

    # Parse ints
    result["bot"]["auto_report_interval"] = int(result["bot"]["auto_report_interval"])
    result["irc"]["port"] = int(result["irc"]["port"])

    return result
