"""Update/upgrade automation plugin for AntiRC bot."""
import logging
import os
import subprocess

from lib import apt, system


class UpdatePlugin:
    """Handle apt update/upgrade and auto-update cron."""

    def __init__(self, config: dict):
        self.cfg = config
        self.bot = None
        self._cron_file = "/etc/cron.d/antircbot-auto-update"

    def bind(self, bot):
        self.bot = bot

    async def handle_command(self, cmd: str, args: list, target: str, source: str, hostmask: str) -> bool:
        handlers = {
            "update": self._cmd_update,
            "upgrade": self._cmd_upgrade,
            "autoupdate": self._cmd_autoupdate,
        }
        handler = handlers.get(cmd)
        if handler:
            await handler(args, target, source, hostmask)
            return True
        return False

    async def _cmd_update(self, args, target, source, hostmask):
        if not self.bot.require_admin(source, hostmask):
            await self.bot.message(target, f"{source}: Access denied.")
            return
        await self.bot.message(target, f"{source}: Running apt update...")
        result = apt.apt_update()
        if result["success"]:
            packages = apt.apt_list_upgradable()
            count = len(packages)
            await self.bot.message(target, f"{source}: apt update complete. {count} packages can be upgraded.")
            if packages:
                pkg_list = ", ".join(packages[:10])
                if len(packages) > 10:
                    pkg_list += f" ... and {len(packages) - 10} more"
                await self.bot.message(target, f"Packages: {pkg_list}")
        else:
            err = result.get("stderr", result.get("error", "unknown error"))
            await self.bot.message(target, f"{source}: apt update failed: {err[:200]}")

    async def _cmd_upgrade(self, args, target, source, hostmask):
        if not self.bot.require_admin(source, hostmask):
            await self.bot.message(target, f"{source}: Access denied.")
            return
        # Confirm if not --force
        if "--force" not in args:
            await self.bot.message(
                target,
                f"{source}: This will run apt upgrade -y. Use !upgrade --force to confirm."
            )
            return
        await self.bot.message(target, f"{source}: Running apt upgrade -y...")
        result = apt.apt_upgrade()
        if result["success"]:
            stdout = result.get("stdout", "")
            # Count upgraded packages
            upgraded = 0
            for line in stdout.split("\n"):
                if "upgraded," in line.lower():
                    try:
                        upgraded = int(line.split()[0])
                    except (ValueError, IndexError):
                        pass
            restart = "\x034REBOOT REQUIRED\x03" if result.get("needs_restart") or apt.check_reboot_required() else ""
            await self.bot.message(
                target,
                f"{source}: Upgrade complete. {upgraded} packages upgraded. {restart}"
            )
            # Autoremove
            auto = apt.apt_autoremove()
            if auto["success"]:
                await self.bot.message(target, f"{source}: Autoremove complete.")
        else:
            err = result.get("stderr", result.get("error", "unknown error"))
            await self.bot.message(target, f"{source}: Upgrade failed: {err[:200]}")

    async def _cmd_autoupdate(self, args, target, source, hostmask):
        if not self.bot.require_admin(source, hostmask):
            await self.bot.message(target, f"{source}: Access denied.")
            return
        if not args:
            # Show status
            if os.path.exists(self._cron_file):
                await self.bot.message(target, f"{source}: Auto-update is \x033ENABLED\x03 ({self._cron_file})")
            else:
                await self.bot.message(target, f"{source}: Auto-update is \x034DISABLED\x03")
            return

        action = args[0].lower()
        if action == "on":
            self._enable_autoupdate()
            await self.bot.message(target, f"{source}: Auto-update \x033ENABLED\x03. Runs daily at 03:00.")
        elif action == "off":
            self._disable_autoupdate()
            await self.bot.message(target, f"{source}: Auto-update \x034DISABLED\x03.")
        else:
            await self.bot.message(target, f"{source}: Usage: !autoupdate [on|off]")

    def _enable_autoupdate(self):
        """Create cron job for auto update + report to IRC."""
        script_path = os.path.join(os.path.dirname(__file__), "../../cron/auto-update.sh")
        cron_content = f"""# AntiRC auto-update cron
SHELL=/bin/bash
PATH=/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin
0 3 * * * root {script_path} >> /var/log/antircbot-auto-update.log 2>&1
"""
        with open(self._cron_file, "w") as f:
            f.write(cron_content)
        os.chmod(self._cron_file, 0o644)
        logging.info("Auto-update cron enabled")

    def _disable_autoupdate(self):
        if os.path.exists(self._cron_file):
            os.remove(self._cron_file)
            logging.info("Auto-update cron disabled")
