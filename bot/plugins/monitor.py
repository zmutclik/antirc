"""Monitoring plugin for AntiRC bot."""
import logging

from lib import system, apt


class MonitorPlugin:
    """Provide system monitoring commands."""

    def __init__(self, config: dict):
        self.cfg = config
        self.bot = None

    def bind(self, bot):
        self.bot = bot

    async def handle_command(self, cmd: str, args: list, target: str, source: str, hostmask: str) -> bool:
        handlers = {
            "status": self._cmd_status,
            "disk": self._cmd_disk,
            "services": self._cmd_services,
            "net": self._cmd_net,
            "docker": self._cmd_docker,
            "logs": self._cmd_logs,
            "alerts": self._cmd_alerts,
        }
        handler = handlers.get(cmd)
        if handler:
            await handler(args, target, source)
            return True
        return False

    async def _cmd_status(self, args, target, source):
        hostname = system.get_hostname()
        uptime = system.get_uptime()
        cpu = system.get_cpu_info()
        mem = system.get_memory_info()

        lines = [
            f"\x02[{hostname}] Status:\x02",
            f"Uptime: {uptime} | Load: {cpu['load1']}/{cpu['load5']}/{cpu['load15']}",
            f"CPU: {cpu['percent']}% ({cpu['cores']} cores)",
            f"RAM: {mem['used']}/{mem['total']} ({mem['percent']}%) | Swap: {mem['swap_used']}/{mem['swap_total']} ({mem['swap_percent']}%)",
        ]
        for line in lines:
            await self.bot.message(target, line)

    async def _cmd_disk(self, args, target, source):
        disks = system.get_disk_info()
        if not disks:
            await self.bot.message(target, "No disk info available.")
            return
        await self.bot.message(target, f"\x02[{system.get_hostname()}] Disk Usage:\x02")
        for d in disks:
            bar = self._progress_bar(d["percent"])
            await self.bot.message(
                target,
                f"{d['mount']} ({d['device']}): {d['used']}/{d['total']} ({d['percent']}%) {bar}"
            )

    async def _cmd_services(self, args, target, source):
        service_name = args[0] if args else None
        services = system.get_service_status(service_name)
        if not services:
            await self.bot.message(target, "No service info available.")
            return
        await self.bot.message(target, f"\x02[{system.get_hostname()}] Services:\x02")
        for s in services[:10]:
            status_color = "\x033" if s["status"] == "active" else "\x034"
            await self.bot.message(target, f"{s['name']}: {status_color}{s['status']}\x03")

    async def _cmd_net(self, args, target, source):
        net = system.get_network_info()
        public_ip = system.get_public_ip()
        if not net:
            await self.bot.message(target, "No network info available.")
            return
        await self.bot.message(target, f"\x02[{system.get_hostname()}] Network:\x02")
        await self.bot.message(target, f"Public IP: {public_ip}")
        for name, info in net.items():
            status = "\x033UP\x03" if info["up"] else "\x034DOWN\x03"
            ips = ", ".join(info["ip4"]) or "no IPv4"
            await self.bot.message(
                target,
                f"{name}: {status} | {ips} | RX: {info['rx']} TX: {info['tx']}"
            )

    async def _cmd_docker(self, args, target, source):
        containers = system.get_docker_info()
        if not containers:
            await self.bot.message(target, "No Docker containers running.")
            return
        await self.bot.message(target, f"\x02[{system.get_hostname()}] Docker:\x02")
        for c in containers[:15]:
            await self.bot.message(
                target,
                f"{c['name']} ({c['image']}): {c['status']}"
            )

    async def _cmd_logs(self, args, target, source):
        service = args[0] if args else None
        lines = int(args[1]) if len(args) > 1 and args[1].isdigit() else 5
        logs = system.get_logs(service, lines)
        log_lines = logs.split("\n")
        await self.bot.message(target, f"\x02[{system.get_hostname()}] Logs ({lines} lines):\x02")
        for line in log_lines[-lines:]:
            if line.strip():
                await self.bot.message(target, line[:400])

    async def _cmd_alerts(self, args, target, source):
        alerts = system.get_security_alerts()
        if not alerts:
            await self.bot.message(target, f"\x02[{system.get_hostname()}] No recent security alerts.\x02")
            return
        await self.bot.message(target, f"\x02[{system.get_hostname()}] Security Alerts (last 10):\x02")
        for alert in alerts:
            await self.bot.message(target, alert[:400])

    async def auto_report(self) -> str:
        """Generate a short auto-report string."""
        hostname = system.get_hostname()
        cpu = system.get_cpu_info()
        mem = system.get_memory_info()
        disks = system.get_disk_info()
        max_disk = max((d["percent"] for d in disks), default=0)
        reboot = apt.check_reboot_required()
        reboot_str = " | \x034REBOOT REQUIRED\x03" if reboot else ""
        return (
            f"\x02[{hostname}]\x02 CPU:{cpu['percent']}% RAM:{mem['percent']}% "
            f"Disk:{max_disk}% Load:{cpu['load1']}{reboot_str}"
        )

    def _progress_bar(self, percent: int, width: int = 10) -> str:
        filled = int(width * percent / 100)
        bar = "█" * filled + "░" * (width - filled)
        return f"[{bar}]"
