FROM emotion_robot_base:latest

COPY ros2_ws /workspace/ros2_ws
RUN /bin/bash -lc "source /opt/ros/humble/setup.bash && cd /workspace/ros2_ws && colcon build"

CMD ["bash", "-lc", "sleep infinity"]
