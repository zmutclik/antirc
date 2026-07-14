"""Authentication plugin for AntiRC bot."""
import logging


class AuthPlugin:
    """Handle admin authentication and management."""

    def __init__(self, config: dict):
        self.cfg = config
        self.bot = None
        self._password = config["auth"]["admin_password"]
        self._require_password = config["auth"]["require_password"]

    def bind(self, bot):
        self.bot = bot

    async def handle_command(self, cmd: str, args: list, target: str, source: str, hostmask: str) -> bool:
        if cmd == "auth":
            return await self._cmd_auth(args, target, source, hostmask)
        if cmd == "addadmin":
            return await self._cmd_addadmin(args, target, source, hostmask)
        if cmd == "deladmin":
            return await self._cmd_deladmin(args, target, source, hostmask)
        if cmd == "admins":
            return await self._cmd_admins(target)
        return False

    async def _cmd_auth(self, args, target, source, hostmask):
        if not args:
            await self.bot.message(target, f"{source}: Usage: !auth <password>")
            return True
        password = args[0]
        if password == self._password:
            self.bot._admins.add(source)
            if hostmask:
                self.bot._admin_hosts[source] = hostmask
            await self.bot.message(target, f"{source}: Authentication successful.")
            logging.info(f"Admin auth success: {source} ({hostmask})")
        else:
            await self.bot.message(target, f"{source}: Authentication failed.")
            logging.warning(f"Admin auth failed: {source} ({hostmask})")
        return True

    async def _cmd_addadmin(self, args, target, source, hostmask):
        if not self.bot.require_admin(source, hostmask):
            await self.bot.message(target, f"{source}: Access denied.")
            return True
        if len(args) < 1:
            await self.bot.message(target, f"{source}: Usage: !addadmin <nick> [hostmask]")
            return True
        nick = args[0]
        self.bot._admins.add(nick)
        if len(args) > 1:
            self.bot._admins.add(args[1])
        await self.bot.message(target, f"{source}: Added {nick} to admin list.")
        logging.info(f"Admin added: {nick} by {source}")
        return True

    async def _cmd_deladmin(self, args, target, source, hostmask):
        if not self.bot.require_admin(source, hostmask):
            await self.bot.message(target, f"{source}: Access denied.")
            return True
        if not args:
            await self.bot.message(target, f"{source}: Usage: !deladmin <nick>")
            return True
        nick = args[0]
        self.bot._admins.discard(nick)
        self.bot._admin_hosts.pop(nick, None)
        await self.bot.message(target, f"{source}: Removed {nick} from admin list.")
        logging.info(f"Admin removed: {nick} by {source}")
        return True

    async def _cmd_admins(self, target):
        admins = ", ".join(sorted(self.bot._admins)) or "None"
        await self.bot.message(target, f"Admins: {admins}")
        return True
