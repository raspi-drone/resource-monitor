import os

class ResourceMonitorNode():
    def __init__(self):
        pass

    def read_cpu_temp(self):
        path = "/sys/class/thermal/thermal_zone0/temp"
    
        if not os.path.exists(path):
            return None
    
        try:
            with open(path, "r") as f:
                return int(f.read().strip()) / 1000.0
        except Exception:
            return None