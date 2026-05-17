import time
import shutil
import subprocess
from dataclasses import dataclass
from typing import Optional


CPU_TEMP_PATH = "/sys/class/thermal/thermal_zone0/temp"
CPU_USAGE_PATH = "/proc/stat"
MEMINFO_PATH = "/proc/meminfo"
NETWORK_PATH = "/proc/net/dev"
DISK_PATH = "/proc/diskstats"


@dataclass
class RpiMetric:
    cpu_temp: Optional[float] = None
    cpu_usage: Optional[float] = None
    cpu_throttle: Optional[str] = None

    ram_total_mb: Optional[float] = None
    ram_used_mb: Optional[float] = None
    ram_free_mb: Optional[float] = None
    ram_usage_percent: Optional[float] = None

    disk_total_gb: Optional[float] = None
    disk_used_gb: Optional[float] = None
    disk_usage_percent: Optional[float] = None

    disk_read: Optional[float] = None
    disk_write: Optional[float] = None

    network_download: Optional[float] = None
    network_upload: Optional[float] = None


class RpiMonitor:
    def __init__(
        self,
        disk_device: str = "mmcblk0",
        network_interface: str = "wlan0",
    ):
        self.disk_device = disk_device
        self.network_interface = network_interface

        # CPU
        self.cpu_last_idle: int | None = None
        self.cpu_last_total: int | None = None

        # Disk IO
        self.last_disk_read: int | None = None
        self.last_disk_write: int | None = None
        self.last_disk_time: float | None = None

        # Network IO
        self.last_net_recv: int | None = None
        self.last_net_sent: int | None = None
        self.last_net_time: float | None = None

    def get_metric(self) -> RpiMetric:
        metric = RpiMetric()

        # CPU
        metric.cpu_temp = self._get_cpu_temp()
        metric.cpu_usage = self._get_cpu_usage()

        throttle = self._get_cpu_throttle_state()
        metric.cpu_throttle = (throttle if throttle else "No throttle active")

        # RAM
        ram_usage = self._get_ram_usage()

        if ram_usage:
            metric.ram_total_mb = ram_usage["total_mb"]
            metric.ram_used_mb = ram_usage["used_mb"]
            metric.ram_free_mb = ram_usage["free_mb"]
            metric.ram_usage_percent = ram_usage["usage_percent"]

        # Disk usage
        disk_usage = self._get_disk_usage()

        if disk_usage:
            metric.disk_total_gb = disk_usage["total_gb"]
            metric.disk_used_gb = disk_usage["used_gb"]
            metric.disk_free_gb = disk_usage["free_gb"]
            metric.disk_usage_percent = disk_usage["usage_percent"]

        # Disk IO
        disk_io = self._get_disk_io()

        if disk_io:
            metric.disk_read = disk_io["read_mb_s"]
            metric.disk_write = disk_io["write_mb_s"]

        # Network IO
        network_io = self._get_network_usage()

        if network_io:
            metric.network_download = network_io[
                "download_mb_s"
            ]
            metric.network_upload = network_io[
                "upload_mb_s"
            ]

        return metric

    def _get_cpu_temp(self) -> float | None:
        try:
            with open(CPU_TEMP_PATH, "r") as f:
                return (
                    int(f.read().strip()) / 1000.0
                )

        except (FileNotFoundError, ValueError, PermissionError,):
            return None

    def _read_cpu_times(self) -> tuple[int | None, int | None]:
        try:
            with open(CPU_USAGE_PATH, "r") as f:
                fields = (f.readline().split()[1:])

            fields = list(map(int, fields))

            idle = fields[3] + fields[4]
            total = sum(fields)

            return idle, total

        except (FileNotFoundError, ValueError, IndexError, PermissionError):
            return None, None

    def _get_cpu_usage(self) -> float | None:
        idle, total = self._read_cpu_times()

        if idle is None or total is None:
            return None

        # First sample
        if (
            self.cpu_last_idle is None
            or self.cpu_last_total is None
        ):
            self.cpu_last_idle = idle
            self.cpu_last_total = total
            return None

        idle_delta = (idle - self.cpu_last_idle)
        total_delta = (total - self.cpu_last_total)

        self.cpu_last_idle = idle
        self.cpu_last_total = total

        if total_delta <= 0:
            return None

        usage = (100.0 * (1.0 - idle_delta / total_delta))

        return round(usage, 2)

    def _get_ram_usage(self) -> dict | None:
        try:
            meminfo = {}

            with open(MEMINFO_PATH, "r") as f:
                for line in f:
                    key, value = line.split(":")
                    meminfo[key] = int(value.strip().split()[0])

            total = meminfo["MemTotal"]
            available = meminfo["MemAvailable"]

            used = total - available

            usage_percent = (
                used / total
            ) * 100

            return {
                "total_mb": round(total / 1024, 2),
                "used_mb": round(used / 1024, 2),
                "free_mb": round(available / 1024, 2),
                "usage_percent": round(usage_percent, 2)
            }

        except (
            FileNotFoundError, KeyError, ValueError, PermissionError):
            return None

    def _get_disk_usage(self, path: str = "/") -> dict | None:
        try:
            total, used, free = (shutil.disk_usage(path))

            return {
                "total_gb": round(total / (1024**3), 2),
                "used_gb": round(used / (1024**3), 2),
                "free_gb": round(free / (1024**3), 2),
                "usage_percent": round((used / total) * 100, 2),
            }

        except PermissionError:
            return None

    def _get_cpu_throttle_state(self) -> str | None:
        try:
            output = (
                subprocess.check_output(
                    [
                        "vcgencmd",
                        "get_throttled",
                    ],
                    text=True,
                ).strip()
            )

            value = int(output.split("=")[1], 16)

            active_states = []

            if value & 0x1:
                active_states.append("under-voltage")

            if value & 0x2:
                active_states.append("frequency-capped")

            if value & 0x4:
                active_states.append("throttled")

            if value & 0x8:
                active_states.append("temperature-limit")

            if not active_states:
                return None

            return ", ".join(active_states)

        except (subprocess.SubprocessError, FileNotFoundError, ValueError, IndexError):
            return None

    def _get_disk_io(self) -> dict:
        empty_result = {
            "read_mb_s": None,
            "write_mb_s": None,
        }

        try:
            with open(DISK_PATH, "r") as f:
                lines = f.readlines()

            for line in lines:
                parts = line.split()

                if (len(parts) < 10 or parts[2] != self.disk_device):
                    continue

                sectors_read = int(parts[5])
                sectors_written = int(parts[9])

                bytes_read = (sectors_read * 512)

                bytes_written = (sectors_written * 512)

                now = time.time()

                # First sample
                if (self.last_disk_read is None
                    or self.last_disk_write is None
                    or self.last_disk_time is None
                ):
                    self.last_disk_read = (bytes_read)
                    self.last_disk_write = (bytes_written)
                    self.last_disk_time = now

                    return empty_result

                elapsed = (now - self.last_disk_time)

                if elapsed <= 0:
                    return empty_result

                read_speed = (bytes_read - self.last_disk_read) / elapsed
                write_speed = (bytes_written - self.last_disk_write) / elapsed

                self.last_disk_read = (bytes_read)
                self.last_disk_write = (bytes_written)
                self.last_disk_time = now

                return {
                    "read_mb_s": round(read_speed / (1024**2), 2),
                    "write_mb_s": round(write_speed / (1024**2), 2),
                }

            return empty_result

        except (FileNotFoundError, ValueError, IndexError, PermissionError):
            return empty_result

    def _get_network_usage(self,) -> dict:
        empty_result = {
            "download_mb_s": None,
            "upload_mb_s": None,
        }

        try:
            with open(NETWORK_PATH, "r") as f:
                lines = f.readlines()

            for line in lines:
                if (self.network_interface + ":") not in line:
                    continue

                parts = line.split()

                recv_bytes = int(parts[1])
                sent_bytes = int(parts[9])

                now = time.time()

                # First sample
                if (self.last_net_recv is None
                    or self.last_net_sent is None
                    or self.last_net_time is None
                ):
                    self.last_net_recv = (recv_bytes)
                    self.last_net_sent = (sent_bytes)
                    self.last_net_time = now

                    return empty_result

                elapsed = (now - self.last_net_time)

                if elapsed <= 0:
                    return empty_result

                download_speed = (recv_bytes - self.last_net_recv) / elapsed
                upload_speed = (sent_bytes - self.last_net_sent) / elapsed

                self.last_net_recv = (recv_bytes)
                self.last_net_sent = (sent_bytes)
                self.last_net_time = now

                return {
                    "download_mb_s": round(download_speed / (1024**2), 2),
                    "upload_mb_s": round(upload_speed / (1024**2), 2)
                }

            return empty_result

        except (FileNotFoundError, ValueError, IndexError, PermissionError):
            return empty_result

