import rclpy
import platform
from rclpy.node import Node
from diagnostic_msgs.msg import DiagnosticArray
from resource_monitor.rpi_monitor.rpi_monitor import RpiMonitor
from resource_monitor.status_builder import StatusBuilder, StatusParameter


class RpiMonitorNode(Node):

    def __init__(self):
        super().__init__('rpi_monitor_node')

        self.declare_parameter('disk_device', 'mmcblk0')
        self.declare_parameter('network_interface', 'wlan0')
        self.declare_parameter('update_rate', 1.0)

        disk_device = self.get_parameter('disk_device').value
        network_interface = self.get_parameter('network_interface').value
        update_rate = self.get_parameter('update_rate').value

        self.rpi_monitor = RpiMonitor(
            disk_device=disk_device,
            network_interface=network_interface,
        )
        self.hardware_id = f"cm5_{platform.node()}".replace("-", "_")

        self.publisher_ = self.create_publisher(DiagnosticArray, '/diagnostics/rpi', 10)

        self.cpu_temp_status = StatusBuilder(self, StatusParameter(
            status_name="cpu_temp", hardware_id=self.hardware_id,
            normal_message="CPU temperature normal",
            warning_threshold=70, warning_message="CPU temperature high",
            error_threshold=80, error_message="CPU overheating"
        ))
        self.cpu_usage_status = StatusBuilder(self, StatusParameter(
            status_name="cpu_usage", hardware_id=self.hardware_id,
            normal_message="CPU usage normal",
            warning_threshold=75, warning_message="CPU usage high",
            error_threshold=90, error_message="CPU usage critical"
        ))
        self.ram_usage_status = StatusBuilder(self, StatusParameter(
            status_name="ram_usage", hardware_id=self.hardware_id,
            normal_message="RAM usage normal",
            warning_threshold=80, warning_message="RAM usage high",
            error_threshold=90, error_message="RAM usage critical"
        ))
        self.disk_space_status = StatusBuilder(self, StatusParameter(
            status_name="disk_space", hardware_id=self.hardware_id,
            normal_message="Disk space normal",
            warning_threshold=80, warning_message="Disk space high",
            error_threshold=90, error_message="Disk space critical"
        ))
        self.disk_write_status = StatusBuilder(self, StatusParameter(
            status_name="disk_write", hardware_id=self.hardware_id,
            normal_message="Disk write normal",
            warning_threshold=20, warning_message="Disk write high",
            error_threshold=30, error_message="Disk write critical"
        ))
        self.disk_read_status = StatusBuilder(self, StatusParameter(
            status_name="disk_read", hardware_id=self.hardware_id,
            normal_message="Disk read normal",
            warning_threshold=50, warning_message="Disk read high",
            error_threshold=60, error_message="Disk read critical"
        ))
        self.network_upload_status = StatusBuilder(self, StatusParameter(
            status_name="network_upload", hardware_id=self.hardware_id,
            normal_message="Network upload normal",
            warning_threshold=10, warning_message="Network upload high",
            error_threshold=15, error_message="Network upload critical"
        ))
        self.network_download_status = StatusBuilder(self, StatusParameter(
            status_name="network_download", hardware_id=self.hardware_id,
            normal_message="Network download normal",
            warning_threshold=10, warning_message="Network download high",
            error_threshold=15, error_message="Network download critical"
        ))

        self.timer = self.create_timer(update_rate, self.timer_callback)
        self.get_logger().info(
            f"Start Raspberry Pi Monitor Node "
            f"(disk={disk_device}, net={network_interface}, rate={update_rate}s)"
        )

    def timer_callback(self):
        data = self.rpi_monitor.get_metric()
        msg = DiagnosticArray()
        msg.header.stamp = self.get_clock().now().to_msg()
        msg.status.append(self.cpu_temp_status.build_status(data.cpu_temp))
        msg.status.append(self.cpu_usage_status.build_status(data.cpu_usage))
        msg.status.append(self.ram_usage_status.build_status(data.ram_usage_percent))
        msg.status.append(self.disk_space_status.build_status(data.disk_usage_percent))
        msg.status.append(self.disk_read_status.build_status(data.disk_read))
        msg.status.append(self.disk_write_status.build_status(data.disk_write))
        msg.status.append(self.network_upload_status.build_status(data.network_upload))
        msg.status.append(self.network_download_status.build_status(data.network_download))
        self.publisher_.publish(msg)


def main(args=None):
    rclpy.init(args=args)
    node = RpiMonitorNode()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()