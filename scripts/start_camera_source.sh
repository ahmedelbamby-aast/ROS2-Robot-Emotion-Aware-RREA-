#!/usr/bin/env bash
set -euo pipefail

source /opt/ros/humble/setup.bash
if [[ -f /workspace/ros2_ws/install/setup.bash ]]; then
  source /workspace/ros2_ws/install/setup.bash
fi

source_mode="${CAMERA_SOURCE:-uvc}"
input_topic="${CAMERA_INPUT_TOPIC:-/camera/image_raw}"
uvc_device="${CAMERA_UVC_DEVICE:-/dev/video0}"
astra_bridge_cmd="${CAMERA_ASTRA_BRIDGE_CMD:-}"

run_uvc() {
  if ros2 pkg executables v4l2_camera 2>/dev/null | rg -q 'v4l2_camera_node'; then
    exec ros2 run v4l2_camera v4l2_camera_node --ros-args \
      -p video_device:="$uvc_device" \
      -r /image_raw:="$input_topic"
  fi
  echo "[camera] UVC requested but v4l2_camera node is unavailable. Provide external publisher on $input_topic."
  exec sleep infinity
}

run_astra() {
  if ros2 pkg executables openni2_camera 2>/dev/null | rg -q 'openni2_camera_node'; then
    exec ros2 run openni2_camera openni2_camera_node --ros-args \
      -r /camera/color/image_raw:="$input_topic" \
      -r /camera/rgb/image_raw:="$input_topic"
  fi
  if [[ -n "$astra_bridge_cmd" ]]; then
    echo "[camera] ASTRA fallback command: $astra_bridge_cmd"
    exec bash -lc "$astra_bridge_cmd"
  fi
  echo "[camera] ASTRA requested but openni2_camera node is unavailable and no astra_bridge_cmd was configured."
  echo "[camera] Fallback hook: set vision.astra_bridge_cmd in config/project.yaml."
  exec sleep infinity
}

case "$source_mode" in
  uvc) run_uvc ;;
  astra) run_astra ;;
  none)
    echo "[camera] source=none, camera publisher intentionally disabled"
    exec sleep infinity
    ;;
  *)
    echo "[camera] invalid source '$source_mode' (expected uvc|astra|none)" >&2
    exit 2
    ;;
esac
