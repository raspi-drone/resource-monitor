FROM ros:jazzy

SHELL ["/bin/sh", "-c"]

ENV RMW_IMPLEMENTATION=rmw_cyclonedds_cpp
ENV ROS_DOMAIN_ID=42

RUN apt-get update && apt-get install -y \
    python3-pip \
    python3-colcon-common-extensions \
    ros-jazzy-rmw-cyclonedds-cpp \
    ros-jazzy-rmw-fastrtps-cpp \
    build-essential \
    git \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /workspace

COPY src ./src

RUN . /opt/ros/jazzy/setup.sh && \
    colcon build --symlink-install

CMD ["/bin/sh", "-c", ". /opt/ros/jazzy/setup.sh && . /workspace/install/setup.sh && ros2 run resource_monitor resource_monitor_node"]