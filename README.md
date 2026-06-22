# Resource-Monitor

ROS 2 node that publishes system resource metrics of a Raspberry Pi as [`diagnostic_msgs/DiagnosticArray`](https://docs.ros.org/en/api/diagnostic_msgs/html/msg/DiagnosticArray.html) on `/diagnostics/rpi`.

Each metric carries its current value plus a rolling statistics window (mean, median, std, min, max) and is classified as `OK`, `WARN`, or `ERROR` against configurable thresholds.

## Metrics

| Status name        | Unit   | Source                                  |
|--------------------|--------|-----------------------------------------|
| `cpu_temp`         | °C     | `/sys/class/thermal/thermal_zone0/temp` |
| `cpu_usage`        | %      | `/proc/stat`                            |
| `ram_usage`        | %      | `/proc/meminfo`                         |
| `disk_space`       | %      | `shutil.disk_usage("/")`               |
| `disk_read`        | MB/s   | `/proc/diskstats`                       |
| `disk_write`       | MB/s   | `/proc/diskstats`                       |
| `network_download` | MB/s   | `/proc/net/dev`                         |
| `network_upload`   | MB/s   | `/proc/net/dev`                         |

CPU throttle state (`under-voltage`, `frequency-capped`, `throttled`, `temperature-limit`) is read via `vcgencmd get_throttled` and attached to the CPU temp status.

## Parameters

| Parameter           | Default   | Description                                              |
|---------------------|-----------|----------------------------------------------------------|
| `disk_device`       | `mmcblk0` | Block device name as it appears in `/proc/diskstats`     |
| `network_interface` | `wwan0`   | Interface name as it appears in `/proc/net/dev`          |
| `update_rate`       | `1.0`     | Publish interval in seconds                              |

## Running with Podman

### Prerequisites

- Podman installed on the Raspberry Pi
- ROS 2 Jazzy running on the host or a separate agent consuming `/diagnostics/rpi`

### Build the image

```bash
git clone https://github.com/raspi-drone/resource-monitor.git
cd resource-monitor
podman build -t resource-monitor .
```

### Run

```bash
podman run --rm \
  --network host \
  --pid host \
  --privileged \
  -v /sys:/sys:ro \
  -v /proc:/proc:ro \
  resource-monitor
```

`--network host` is required so the node can reach other ROS 2 participants via DDS.
`--pid host` and `/proc` bind-mount give the node access to the host's process and hardware stats.
`--privileged` is needed for `vcgencmd` to access `/dev/vcio` for CPU throttle state.

### Passing parameters

Parameters are forwarded as launch arguments:

```bash
podman run --rm \
  --network host \
  --pid host \
  --privileged \
  -v /sys:/sys:ro \
  -v /proc:/proc:ro \
  resource-monitor \
  disk_device:=sda \
  network_interface:=eth0 \
  update_rate:=2.0
```

### Run as a systemd service

```bash
podman run -d \
  --name resource-monitor \
  --restart unless-stopped \
  --network host \
  --pid host \
  --privileged \
  -v /sys:/sys:ro \
  -v /proc:/proc:ro \
  resource-monitor

podman generate systemd --new --name resource-monitor \
  > ~/.config/systemd/user/resource-monitor.service

systemctl --user daemon-reload
systemctl --user enable --now resource-monitor
```

## Default thresholds

| Metric             | WARN    | ERROR   |
|--------------------|---------|---------|
| `cpu_temp`         | 70 °C   | 80 °C   |
| `cpu_usage`        | 75 %    | 90 %    |
| `ram_usage`        | 80 %    | 90 %    |
| `disk_space`       | 80 %    | 90 %    |
| `disk_read`        | 50 MB/s | 60 MB/s |
| `disk_write`       | 20 MB/s | 30 MB/s |
| `network_upload`   | 10 MB/s | 15 MB/s |
| `network_download` | 10 MB/s | 15 MB/s |

## Topic

```
/diagnostics/rpi  →  diagnostic_msgs/msg/DiagnosticArray
```

Each `DiagnosticStatus` in the array contains:

```
name:        <metric name>
hardware_id: cm5_<hostname>
level:       0 (OK) | 1 (WARN) | 2 (ERROR)
message:     human-readable description
values:
  - key: <metric name>   value: <current value>
  - key: mean            value: ...
  - key: median          value: ...
  - key: std             value: ...
  - key: min             value: ...
  - key: max             value: ...
```

Statistics are calculated over a rolling window of the last 1000 samples.

## Verifying output

On any machine sharing the same ROS 2 domain:

```bash
ros2 topic echo /diagnostics/rpi
```

Check individual status levels:

```bash
ros2 topic echo /diagnostics/rpi --field status[0].level
# 0 = OK  |  1 = WARN  |  2 = ERROR
```