# =========================================================
# STAGE 1: Builder
# =========================================================
FROM docker.io/library/ros:jazzy AS builder

ENV RMW_IMPLEMENTATION=rmw_cyclonedds_cpp

# Install build dependencies
RUN apt-get update && apt-get install -y \
    python3-pip \
    python3-colcon-common-extensions \
    ros-jazzy-rmw-cyclonedds-cpp \
    ros-jazzy-rmw-fastrtps-cpp \
    build-essential \
    git \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /workspace

# Copy source
COPY src ./src

# Build workspace (IMPORTANT: bash explicitly + source ROS correctly)
RUN /bin/bash -c "source /opt/ros/jazzy/setup.bash && colcon build --symlink-install"


# =========================================================
# STAGE 2: Runtime
# =========================================================
FROM docker.io/library/ros:jazzy AS runtime

ENV RMW_IMPLEMENTATION=rmw_cyclonedds_cpp

# Minimal runtime deps
RUN apt-get update && apt-get install -y \
    ros-jazzy-rmw-cyclonedds-cpp \
    ros-jazzy-rmw-fastrtps-cpp \
    python3 \
    && rm -rf /var/lib/apt/lists/*

# -------------------------
# Non-root user (FIXED)
# -------------------------
ARG USERNAME=drone
ARG USER_UID=1000
ARG USER_GID=1000

RUN set -eux; \
    if ! getent group ${USER_GID}; then \
        groupadd --gid ${USER_GID} ${USERNAME}; \
    else \
        GROUP_NAME=$(getent group ${USER_GID} | cut -d: -f1); \
        usermod -l ${USERNAME} -d /home/${USERNAME} -m ${GROUP_NAME} 2>/dev/null || true; \
    fi; \
    if ! id -u ${USERNAME} >/dev/null 2>&1; then \
        useradd --uid ${USER_UID} --gid ${USER_GID} -m ${USERNAME}; \
    fi

# Copy built workspace
COPY --from=builder /workspace/install /opt/ros_ws/install

# -------------------------
# ROS environment setup
# -------------------------
RUN echo "source /opt/ros/jazzy/setup.bash" >> /home/${USERNAME}/.bashrc && \
    echo "source /opt/ros_ws/install/setup.bash" >> /home/${USERNAME}/.bashrc

RUN chown -R ${USERNAME}:${USERNAME} /home/${USERNAME}

USER ${USERNAME}
WORKDIR /home/${USERNAME}

# -------------------------
# Entrypoint
# -------------------------
ENTRYPOINT ["/bin/bash", "-c", "source /opt/ros/jazzy/setup.bash && source /opt/ros_ws/install/setup.bash && exec bash"]