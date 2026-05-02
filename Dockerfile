FROM ros:jazzy

# Use bash only for convenience tools, not required for build
SHELL ["/bin/sh", "-c"]

ENV RMW_IMPLEMENTATION=rmw_cyclonedds_cpp

# Install dependencies
RUN apt-get update && apt-get install -y \
    python3-pip \
    python3-colcon-common-extensions \
    ros-jazzy-rmw-cyclonedds-cpp \
    ros-jazzy-rmw-fastrtps-cpp \
    build-essential \
    git \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /workspace

# Copy workspace
COPY src ./src

# Build ROS2 workspace (POSIX-compliant)
RUN . /opt/ros/jazzy/setup.sh && \
    colcon build --symlink-install

# Source workspace on container start
CMD ["/bin/sh", "-c", ". /opt/ros/jazzy/setup.sh && . /workspace/install/setup.sh && bash"]