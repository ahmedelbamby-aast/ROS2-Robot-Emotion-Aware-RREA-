#!/usr/bin/env bash
set -euo pipefail

# ROS melodic setup scripts can reference unset vars; relax nounset while sourcing.
set +u
source /opt/ros/melodic/setup.bash
source "$HOME/catkin_ws/devel/setup.bash"
set -u

pkill -f roscore || true
pkill -f roslaunch || true
pkill -f astra_camera || true

mkdir -p /tmp/roslogs
nohup roscore >/tmp/roslogs/roscore.log 2>&1 &
sleep 3
nohup roslaunch rchomeedu_vision multi_astra.launch >/tmp/roslogs/multi_astra.log 2>&1 &
sleep 12

echo "[astra-host] camera topics:"
rostopic list | grep -E '^/camera($|_)|^/camera_top' | head -n 40 || true

echo "[astra-host] rgb hz /camera_top/rgb/image_raw:"
timeout 10s rostopic hz /camera_top/rgb/image_raw -w 5 || true
