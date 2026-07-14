#!/usr/bin/env python3
"""AntiRC - IRC Bot for Linux server monitoring and update automation."""
import asyncio
import logging
import os
import sys
import time
from pathlib import Path

import pydle

from config import load_config


class AntiRCBot(pydle.Client):
    """Main IRC bot class with plugin system."""

    def __init__(self, config: dict, **kwargs):
        self.cfg = config
        self.plugins = {}
        self._admins = set(self.cfg["auth"]["admins"])
        self._admin_hosts = {}  # nick -> hostmask
        self._auto_report_task = None
        super().__init__(
            self.cfg["irc"]["nick"],
            realname=self.cfg["irc"]["realname"],
            **kwargs,
        )

    # ------------------------------------------------------------------
    # Lifecycle
    # ------------------------------------------------------------------
    async def on_connect(self):
        await super().on_connect()
        channel = self.cfg["irc"]["channel"]
        key = self.cfg["irc"]["channel_key"]
        if key:
            await self.join(channel, key)
        else:
            await self.join(channel)
        logging.info(f"Connected and joined {channel}")
        await self.message(channel, f"\x02AntiRC\x02 bot online. Host: {os.uname().nodename}")
        self._start_auto_report()

    async def on_disconnect(self, expected):
        logging.warning("Disconnected from IRC server")
        if self._auto_report_task:
            self._auto_report_task.cancel()
        await super().on_disconnect(expected)

    # ------------------------------------------------------------------
    # Plugin system
    # ------------------------------------------------------------------
    def register_plugin(self, name: str, plugin):
        self.plugins[name] = plugin
        plugin.bind(self)
        logging.info(f"Plugin registered: {name}")

    # ------------------------------------------------------------------
    # Auth helpers
    # ------------------------------------------------------------------
    def is_admin(self, nick: str, hostmask: str = None) -> bool:
        if nick in self._admins:
            return True
        if hostmask and hostmask in self._admins:
            return True
        return False

    def require_admin(self, nick: str, hostmask: str) -> bool:
        if self.is_admin(nick, hostmask):
            return True
        return False

    # ------------------------------------------------------------------
    # Message handlers
    # ------------------------------------------------------------------
    async def on_message(self, target, source, message):
        await super().on_message(target, source, message)
        if source == self.nickname:
            return

        # Only respond to commands in channel or PM
        if not message.startswith("!"):
            return

        parts = message[1:].split()
        if not parts:
            return
        cmd = parts[0].lower()
        args = parts[1:]

        # Get hostmask from user info if available
        hostmask_str = None
        try:
            if hasattr(self, 'users') and source in self.users:
                user = self.users[source]
                if hasattr(user, 'username') and hasattr(user, 'hostname'):
                    hostmask_str = f"{source}!{user.username}@{user.hostname}"
        except Exception:
            pass

        handled = False
        for plugin in self.plugins.values():
            if hasattr(plugin, "handle_command"):
                try:
                    result = await plugin.handle_command(cmd, args, target, source, hostmask_str)
                    if result:
                        handled = True
                        break
                except Exception as e:
                    logging.exception(f"Plugin error: {e}")
                    await self.message(target, f"\x034Error:\x03 {e}")
                    handled = True
                    break

        if not handled and cmd == "help":
            await self._show_help(target)

    async def _show_help(self, target):
        lines = [
            "\x02AntiRC Commands:\x02",
            "!status — CPU, memory, load, uptime",
            "!disk — Disk usage",
            "!services [name] — Systemd service status",
            "!net — Network stats",
            "!docker — Docker container status",
            "!logs [service] [lines] — Recent logs",
            "!alerts — Security alerts",
            "!update — Check for apt updates",
            "!upgrade — Run apt upgrade",
            "!autoupdate — Toggle auto-update cron",
            "!help — Show this help",
        ]
        for line in lines:
            await self.message(target, line)

    # ------------------------------------------------------------------
    # Auto report
    # ------------------------------------------------------------------
    def _start_auto_report(self):
        interval = self.cfg["bot"]["auto_report_interval"]
        if interval > 0:
            self._auto_report_task = asyncio.create_task(self._auto_report_loop(interval))

    async def _auto_report_loop(self, interval: int):
        channel = self.cfg["irc"]["channel"]
        while True:
            await asyncio.sleep(interval)
            try:
                monitor = self.plugins.get("monitor")
                if monitor and hasattr(monitor, "auto_report"):
                    report = await monitor.auto_report()
                    if report:
                        await self.message(channel, report)
            except Exception as e:
                logging.exception(f"Auto-report error: {e}")


# ----------------------------------------------------------------------
# Entry point
# ----------------------------------------------------------------------
def main():
    config_path = os.environ.get("ANTIRC_CONFIG", "config.ini")
    cfg = load_config(config_path)

    # Setup logging
    log_file = cfg["bot"]["log_file"]
    Path(log_file).parent.mkdir(parents=True, exist_ok=True)
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(message)s",
        handlers=[
            logging.FileHandler(log_file),
            logging.StreamHandler(sys.stdout),
        ],
    )

    # Create data dir
    data_dir = Path(cfg["bot"]["data_dir"])
    data_dir.mkdir(parents=True, exist_ok=True)

    # Init bot
    tls = cfg["irc"]["tls"]
    bot = AntiRCBot(cfg)

    # Load plugins
    from plugins.auth import AuthPlugin
    from plugins.monitor import MonitorPlugin
    from plugins.update import UpdatePlugin

    bot.register_plugin("auth", AuthPlugin(cfg))
    bot.register_plugin("monitor", MonitorPlugin(cfg))
    bot.register_plugin("update", UpdatePlugin(cfg))

    # Connect
    host = cfg["irc"]["host"]
    port = cfg["irc"]["port"]
    logging.info(f"Connecting to {host}:{port} (TLS={tls})...")

    async def run_bot():
        await bot.connect(host, port, tls=tls, tls_verify=False)
        await bot.handle_forever()

    asyncio.run(run_bot())


if __name__ == "__main__":
    main()
