# =========================
# Builder stage
# =========================
FROM ros:jazzy AS builder

SHELL ["/bin/bash", "-c"]

ENV RMW_IMPLEMENTATION=rmw_cyclonedds_cpp

RUN apt-get update && apt-get install -y \
    python3-pip \
    python3-colcon-common-extensions \
    ros-jazzy-rmw-cyclonedds-cpp \
    ros-jazzy-rmw-fastrtps-cpp \
    build-essential \
    git \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /workspace

# Copy workspace source
COPY src ./src

# Build ROS workspace
RUN source /opt/ros/jazzy/setup.bash && \
    colcon build --symlink-install


# =========================
# Runtime stage
# =========================
FROM ros:jazzy AS runtime

SHELL ["/bin/bash", "-c"]

ENV RMW_IMPLEMENTATION=rmw_cyclonedds_cpp

RUN apt-get update && apt-get install -y \
    ros-jazzy-rmw-cyclonedds-cpp \
    ros-jazzy-rmw-fastrtps-cpp \
    python3 \
    && rm -rf /var/lib/apt/lists/*

# -------------------------
# Create non-root user safely
# -------------------------
ARG USERNAME=drone
ARG USER_UID=1000
ARG USER_GID=1000

RUN set -eux; \
    if ! getent group ${USER_GID}; then \
        groupadd --gid ${USER_GID} ${USERNAME}; \
    else \
        EXISTING_GROUP=$(getent group ${USER_GID} | cut -d: -f1); \
        groupmod -n ${USERNAME} ${EXISTING_GROUP} || true; \
    fi; \
    if ! id -u ${USERNAME} >/dev/null 2>&1; then \
        useradd --uid ${USER_UID} --gid ${USER_GID} -m ${USERNAME}; \
    fi

# Workspace setup
WORKDIR /opt/ros_ws

COPY --from=builder /workspace/install ./install

# Source ROS + workspace automatically
RUN echo "source /opt/ros/jazzy/setup.bash" >> /home/${USERNAME}/.bashrc && \
    echo "source /opt/ros_ws/install/setup.bash" >> /home/${USERNAME}/.bashrc

# Fix permissions safely
RUN chown -R ${USER_UID}:${USER_GID} /home/${USERNAME}

USER ${USERNAME}

CMD ["bash"]