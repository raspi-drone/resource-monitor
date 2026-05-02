import os

import rclpy
from rclpy.node import Node

from diagnostic_msgs.msg import DiagnosticArray, DiagnosticStatus, KeyValue
from .resource_monitor_node import ResourceMonitorNode

import platform


class ResourceMonitor(Node):

    def __init__(self):
        super().__init__('resource_monitor')
        
        self.resource_monitor_node = ResourceMonitorNode()

        self.publisher_ = self.create_publisher(
            DiagnosticArray,
            '/diagnostics',
            10
        )

        self.timer = self.create_timer(1.0, self.timer_callback)


    def timer_callback(self):
        temp = self.resource_monitor_node.read_cpu_temp()

        msg = DiagnosticArray()
        msg.header.stamp = self.get_clock().now().to_msg()

        status = DiagnosticStatus()
        status.name = "CPU Temperature"
        status.hardware_id = f"cm5_{platform.node()}"

        if temp is None:
            status.level = DiagnosticStatus.ERROR
            status.message = "Temperature unavailable"
        else:
            status.values.append(KeyValue(key="cpu_temperature_c", value=str(temp)))

            # Simple thresholds
            if temp < 70:
                status.level = DiagnosticStatus.OK
                status.message = "CPU temperature normal"
            elif temp < 80:
                status.level = DiagnosticStatus.WARN
                status.message = "CPU temperature high"
            else:
                status.level = DiagnosticStatus.ERROR
                status.message = "CPU overheating"

        msg.status.append(status)

        self.publisher_.publish(msg)

        self.get_logger().info(
            f"CPU Temp: {temp:.2f} °C" if temp else "CPU Temp: unavailable"
        )


def main(args=None):
    rclpy.init(args=args)
    node = ResourceMonitor()
    rclpy.spin(node)
    node.destroy_node()
    rclpy.shutdown()


if __name__ == '__main__':
    main()