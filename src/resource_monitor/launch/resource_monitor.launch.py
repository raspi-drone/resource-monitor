from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node


def generate_launch_description():
    return LaunchDescription([
        DeclareLaunchArgument('disk_device', default_value='mmcblk0',
                              description='Disk device to monitor (e.g. mmcblk0, sda)'),
        DeclareLaunchArgument('network_interface', default_value='wwan0',
                              description='Network interface to monitor (e.g. wlan0, eth0)'),
        DeclareLaunchArgument('update_rate', default_value='1.0',
                              description='Publish rate in seconds'),
        Node(
            package='resource_monitor',
            executable='rpi_monitor_node',
            name='rpi_monitor_node',
            parameters=[{
                'disk_device': LaunchConfiguration('disk_device'),
                'network_interface': LaunchConfiguration('network_interface'),
                'update_rate': LaunchConfiguration('update_rate'),
            }],
            output='screen',
        ),
    ])