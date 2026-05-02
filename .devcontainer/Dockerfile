FROM ros:jazzy

ARG USERNAME=drone
ARG USER_UID=1000
ARG USER_GID=$USER_UID

# Delete user if it exists in container (e.g Ubuntu Noble: ubuntu)
RUN if id -u $USER_UID ; then userdel `id -un $USER_UID` ; fi

# Create the user
RUN groupadd --gid $USER_GID $USERNAME \
    && useradd --uid $USER_UID --gid $USER_GID -m $USERNAME \
    && apt-get update \
    && apt-get install -y sudo \
    && echo $USERNAME ALL=\(root\) NOPASSWD:ALL > /etc/sudoers.d/$USERNAME \
    && chmod 0440 /etc/sudoers.d/$USERNAME

# =========================================================
# ROS 2 + DDS dependencies (THIS FIXES YOUR ERROR)
# =========================================================
RUN apt-get update && apt-get install -y \
    python3-pip \
    ros-jazzy-rmw-cyclonedds-cpp \
    ros-jazzy-rmw-fastrtps-cpp \
    && rm -rf /var/lib/apt/lists/*

ENV SHELL=/bin/bash

# Optional: default DDS implementation (safe for your setup)
ENV RMW_IMPLEMENTATION=rmw_cyclonedds_cpp

# Switch to non-root user
USER $USERNAME

CMD ["/bin/bash"]