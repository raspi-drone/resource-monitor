# ROS2 - Resource Monitor Node

how to run:
```bash
podman run -itd --name resource-monitor --privileged --network=host --ipc=host   --security-opt label=disable ghcr.io/raspi-drone/resource-monitor:latest
```

on host (for cpu throttle state):
```bash
sudo chmod 666 /dev/vcio
```