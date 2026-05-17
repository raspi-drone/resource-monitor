#!/bin/bash
set -e

source /opt/ros/jazzy/setup.bash
source install/setup.bash 

exec ros2 run resource_monitor rpi_monitor_node