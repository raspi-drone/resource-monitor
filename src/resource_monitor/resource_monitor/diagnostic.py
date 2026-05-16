from typing import Optional

from rclpy.node import Node
from diagnostic_msgs.msg import DiagnosticArray, DiagnosticStatus, KeyValue
from dataclasses import dataclass

@dataclass
class DiagnosticParameter:
    status_name: str
    hardware_id: str
    normal_message: Optional[str]
    warning_threshold: Optional[float]
    warning_message: Optional[str]
    error_threshold: Optional[float]
    error_message: Optional[str]
    




class DiagnosticPublisher:
    def __init__(self, node: Node, diagnostic_parameter: DiagnosticParameter):
        self.node = node
        self.diagnostic_parameter = diagnostic_parameter
        
        self.publisher = node.create_publisher(
            DiagnosticArray,
            f'/diagnostics/{diagnostic_parameter.hardware_id}/{diagnostic_parameter.status_name}',
            10
        )
    
    def publish(self, data: float | str):
        msg = DiagnosticArray()
        msg.header.stamp = self.node.get_clock().now().to_msg()

        status = DiagnosticStatus()
        status.name = self.diagnostic_parameter.status_name
        status.hardware_id = self.diagnostic_parameter.hardware_id
        
        status = DiagnosticStatus()
        
        if data is not None and type(data) == float:
            status.values.append(KeyValue(key=self.diagnostic_parameter.status_name, value=str(data)))
            
            if data < self.diagnostic_parameter.warning_threshold:
                status.level = DiagnosticStatus.OK
                status.message = self.diagnostic_parameter.normal_message
            elif data < self.diagnostic_parameter.error_threshold:
                status.level = DiagnosticStatus.WARN
                status.message = self.diagnostic_parameter.warning_message
            else:
                status.level = DiagnosticStatus.ERROR
                status.message = self.diagnostic_parameter.error_message

        msg.status.append(status)
        self.publisher.publish(msg)

        self.node.get_logger().info(
            f"{self.diagnostic_parameter.status_name} {data:.2f}" if data else f"{self.diagnostic_parameter.status_name}: unavailable"
        )