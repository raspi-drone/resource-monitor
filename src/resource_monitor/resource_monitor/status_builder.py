from collections import deque
from typing import Optional

from rclpy.node import Node
from diagnostic_msgs.msg import DiagnosticArray, DiagnosticStatus, KeyValue
from dataclasses import dataclass
import numpy as np

@dataclass
class StatusParameter:
    status_name: str
    hardware_id: str
    normal_message: Optional[str]
    warning_threshold: Optional[float]
    warning_message: Optional[str]
    error_threshold: Optional[float]
    error_message: Optional[str]
    
@dataclass    
class StatusStatistic:
    mean: float
    median: float
    std: float
    min: float
    max: float
    
        
class StatusBuilder:
    def __init__(self, node: Node, diagnostic_parameter: StatusParameter, history_length: float = 1000):
        self.node = node
        self.diagnostic_parameter = diagnostic_parameter
        
        self.history: list[float] = deque(maxlen=history_length)

    
    def build_status(self, data: float | str) -> DiagnosticStatus:
        status = DiagnosticStatus()
        status.name = self.diagnostic_parameter.status_name
        status.hardware_id = self.diagnostic_parameter.hardware_id
        
        if data is not None and type(data) == float:
            statistics = self._calculate_statistics(data)
            
            status.values.append(KeyValue(key=self.diagnostic_parameter.status_name, value=str(data)))
            status.values.append(KeyValue(key='mean', value=str(statistics.mean)))
            status.values.append(KeyValue(key='median', value=str(statistics.median)))
            status.values.append(KeyValue(key='std', value=str(statistics.std)))
            status.values.append(KeyValue(key='min', value=str(statistics.min)))
            status.values.append(KeyValue(key='max', value=str(statistics.max)))
            
            if data < self.diagnostic_parameter.warning_threshold:
                status.level = DiagnosticStatus.OK
                status.message = self.diagnostic_parameter.normal_message
            elif data < self.diagnostic_parameter.error_threshold:
                status.level = DiagnosticStatus.WARN
                status.message = self.diagnostic_parameter.warning_message
            else:
                status.level = DiagnosticStatus.ERROR
                status.message = self.diagnostic_parameter.error_message
                

        self.node.get_logger().info(
            f"{self.diagnostic_parameter.status_name} {data:.2f}" if data else f"{self.diagnostic_parameter.status_name}: unavailable"
        )
        
        return status
    
    def _calculate_statistics(self, data: float) -> StatusStatistic:
        self.history.append(data)

        values = np.asarray(self.history)

        return StatusStatistic(
            mean=round(float(np.mean(values)), 2),
            median=round(float(np.median(values)), 2),
            std=round(float(np.std(values)), 2),
            min=round(float(np.min(values)), 2),
            max=round(float(np.max(values)), 2),
        )
        