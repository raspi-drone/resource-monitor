# =========================================================
# STAGE 1: Build stage (compilation + dependencies)
# =========================================================
FROM docker.io/library/ros:jazzy AS builder

SHELL ["/bin/bash", "-c"]

# Build dependencies
RUN apt-get update && apt-get install -y \
    python3-pip \
    python3-colcon-common-extensions \
    ros-jazzy-rmw-cyclonedds-cpp \
    ros-jazzy-rmw-fastrtps-cpp \
    build-essential \
    git \
    && rm -rf /var/lib/apt/lists/*

ENV RMW_IMPLEMENTATION=rmw_cyclonedds_cpp

# Workspace
WORKDIR /workspace

# Copy source code
# (adjust if your repo structure differs)
COPY src ./src

# Build ROS 2 workspace
RUN source /opt/ros/jazzy/setup.bash && \
    colcon build --symlink-install

# =========================================================
# STAGE 2: Runtime stage (minimal + production hardened)
# =========================================================
FROM docker.io/library/ros:jazzy AS runtime

SHELL ["/bin/bash", "-c"]

# Minimal runtime dependencies only
RUN apt-get update && apt-get install -y \
    ros-jazzy-rmw-cyclonedds-cpp \
    ros-jazzy-rmw-fastrtps-cpp \
    python3 \
    && rm -rf /var/lib/apt/lists/*

# DDS configuration (important for ROS 2 discovery in Podman)
ENV RMW_IMPLEMENTATION=rmw_cyclonedds_cpp

# Create non-root user (safer production practice)
ARG USERNAME=drone
ARG USER_UID=1000
ARG USER_GID=1000

RUN groupadd --gid ${USER_GID} ${USERNAME} && \
    useradd --uid ${USER_UID} --gid ${USER_GID} -m ${USERNAME}

# Copy built workspace from builder stage
COPY --from=builder /workspace/install /opt/ros_ws/install

# Source overlay automatically
RUN echo "source /opt/ros/ jazzy/setup.bash" >> /home/${USERNAME}/.bashrc && \
    echo "source /opt/ros_ws/install/setup.bash" >> /home/${USERNAME}/.bashrc

# Fix permissions
RUN chown -R ${USERNAME}:${USERNAME} /home/${USERNAME}

USER ${USERNAME}

WORKDIR /home/${USERNAME}

# =========================================================
# Entrypoint (clean ROS startup behavior)
# =========================================================
ENTRYPOINT ["/bin/bash", "-c", "source /opt/ros/jazzy/setup.bash && source /opt/ros_ws/install/setup.bash && exec bash"]