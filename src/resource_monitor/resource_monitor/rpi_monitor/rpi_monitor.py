import os
import shutil
import subprocess
from dataclasses import dataclass

CPU_TEMP_PATH = "/sys/class/thermal/thermal_zone0/temp"
CPU_USAGE_PATH = "/proc/stat"
MEMINFO_PATH = "/proc/meminfo"

@dataclass
class RpiMetric:
    cpu_temp: float | None = None
    cpu_usage: float | None = None
    cpu_throttle: str | None = None

    ram_total_mb: float | None = None
    ram_used_mb: float | None = None
    ram_free_mb: float | None = None
    ram_usage_percent: float | None = None

    disk_total_gb: float | None = None
    disk_used_gb: float | None = None
    disk_free_gb: float | None = None
    disk_usage_percent: float | None = None


class RpiMonitor:
    def __init__(self):
        self.cpu_last_idle = 0
        self.cpu_last_total = 0
        
    def get_metric(self) -> RpiMetric:
        metric = RpiMetric()
        
        metric.cpu_temp = self._get_cpu_temp()
        metric.cpu_usage = self._get_cpu_usage()
        metric.cpu_throttle = self._get_cpu_throttle_state() or "No throttle active"
        
        ram_usage = self._get_ram_usage()
        metric.ram_total_mb = ram_usage["total_mb"]
        metric.ram_free_mb = ram_usage["free_mb"]
        metric.ram_used_mb =  ram_usage["used_mb"]
        metric.ram_usage_percent = ram_usage["usage_percent"]
        
        disk_usage = self._get_disk_usage()
        metric.disk_total_gb = disk_usage["total_gb"]
        metric.disk_used_gb = disk_usage["used_gb"]
        metric.disk_free_gb = disk_usage["free_gb"]
        metric.disk_usage_percent = disk_usage["usage_percent"]
        
        return metric

    def _get_cpu_temp(self):
        try:
            with open(CPU_TEMP_PATH, "r") as f:
                return int(f.read().strip()) / 1000.0
        except (FileNotFoundError, ValueError, PermissionError):
            return None
        

    def _get_cpu_usage(self):
        try:
            idle, total = self._read_cpu_times()

            if idle is None or total is None:
                return None

            # first call
            if self.cpu_last_total == 0:
                self.cpu_last_idle = idle
                self.cpu_last_total = total
                return None

            idle_delta = idle - self.cpu_last_idle
            total_delta = total - self.cpu_last_total

            self.cpu_last_idle = idle
            self.cpu_last_total = total

            if total_delta <= 0:
                return 0.0

            usage = 100.0 * (1.0 - idle_delta / total_delta)

            return round(usage, 2)

        except (FileNotFoundError, ValueError, PermissionError) as e:
            return None
        
        
    def _read_cpu_times(self):
        try:
            with open(CPU_USAGE_PATH, "r") as f:
                fields = f.readline().split()[1:]

            fields = list(map(int, fields))

            idle = fields[3] + fields[4]  # idle + iowait
            total = sum(fields)

            return idle, total

        except (FileNotFoundError, ValueError, IndexError, PermissionError) as e:
            return None
        
        
    def _get_ram_usage(self):
        try:
            meminfo = {}

            with open(MEMINFO_PATH, "r") as f:
                for line in f:
                    key, value = line.split(":")
                    meminfo[key] = int(value.strip().split()[0])

            total = meminfo["MemTotal"]
            available = meminfo["MemAvailable"]

            used = total - available
            usage_percent = (used / total) * 100

            return {
                "total_mb": round(total / 1024, 2),
                "used_mb": round(used / 1024, 2),
                "free_mb": round(available / 1024, 2),
                "usage_percent": round(usage_percent, 2)
            }

        except (FileNotFoundError, KeyError, ValueError, PermissionError):
            return None


    def _get_disk_usage(self, path="/"):
        try:
            total, used, free = shutil.disk_usage(path)

            return {
                "total_gb": round(total / (1024**3), 2),
                "used_gb": round(used / (1024**3), 2),
                "free_gb": round(free / (1024**3), 2),
                "usage_percent": round((used / total) * 100, 2)
            }

        except PermissionError:
            return None


    def _get_cpu_throttle_state(self):

        try:
            output = subprocess.check_output(
                ["vcgencmd", "get_throttled"],
                text=True
            ).strip()

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

            # Return None when system is healthy
            if not active_states:
                return None

            return ", ".join(active_states)

        except Exception as e:
            raise RuntimeError(
                f"Failed to read throttle state: {e}"
            )