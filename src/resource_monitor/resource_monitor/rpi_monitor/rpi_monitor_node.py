import rclpy
import platform
from rclpy.node import Node
from diagnostic_msgs.msg import DiagnosticArray, DiagnosticStatus, KeyValue
from resource_monitor.rpi_monitor.rpi_monitor import RpiMonitor, RpiMetric
from resource_monitor.diagnostic import DiagnosticPublisher, DiagnosticParameter
import platform

class RpiMonitorNode(Node):

    def __init__(self):
        super().__init__('rpi_monitor_node')
        
        self.rpi_monitor = RpiMonitor()
        self.hardware_id = f"cm5_{platform.node()}".replace("-", "_")

        # self.publisher_ = self.create_publisher(
        #     DiagnosticArray,
        #     '/diagnostics/rpi',
        #     10
        # )
        
        self.cpu_temp_publisher = DiagnosticPublisher(self, DiagnosticParameter(
            status_name="cpu_temp",
            hardware_id=self.hardware_id,
            normal_message="CPU temperature normal",
            warning_threshold=70,
            warning_message="CPU temperature high",
            error_threshold=80,
            error_message="CPU overheating"
        ))
        
        self.cpu_usage_publisher = DiagnosticPublisher(self, DiagnosticParameter(
            status_name="cpu_usage",
            hardware_id=self.hardware_id,
            normal_message="CPU usage normal",
            warning_threshold=75,
            warning_message="CPU usage high",
            error_threshold=90,
            error_message="CPU usage critical"
        ))

        self.timer = self.create_timer(1.0, self.timer_callback)


    def timer_callback(self):
        data = self.rpi_monitor.get_metric()
        
        self.cpu_temp_publisher.publish(data.cpu_temp)
        self.cpu_usage_publisher.publish(data.cpu_usage)

        # msg = DiagnosticArray()
        # msg.header.stamp = self.get_clock().now().to_msg()


        # msg.status.append(status)

        # self.publisher_.publish(msg)
        
        



def main(args=None):
    rclpy.init(args=args)
    node = RpiMonitorNode()
    rclpy.spin(node)
    node.destroy_node()
    rclpy.shutdown()


if __name__ == '__main__':
    main()