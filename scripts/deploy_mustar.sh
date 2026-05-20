#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

COMPOSE_FILE="docker/docker-compose.yml"
COMPOSE=(docker compose -f "$COMPOSE_FILE")
VIDEO_PRIMARY="${VIDEO_DEVICE_PRIMARY:-/dev/video0}"
VIDEO_SECONDARY="${VIDEO_DEVICE_SECONDARY:-/dev/video1}"
ALLOW_NO_VIDEO="${ALLOW_NO_VIDEO:-0}"
MODE_OVERRIDE="${1:-}"

usage() {
  cat <<USAGE
Usage: scripts/deploy_mustar.sh [robot_only|laptop_offload]

One-command Mustar deployment:
1) Verify host + container camera/mic/speaker devices
2) Build docker images and ros2_ws
3) Launch the correct bringup for deployment.mode

If mode argument is omitted, deployment.mode from config/project.yaml is used.
USAGE
}

if [[ "$MODE_OVERRIDE" == "-h" || "$MODE_OVERRIDE" == "--help" ]]; then
  usage
  exit 0
fi

if [[ -n "$MODE_OVERRIDE" && "$MODE_OVERRIDE" != "robot_only" && "$MODE_OVERRIDE" != "laptop_offload" ]]; then
  echo "Invalid mode: $MODE_OVERRIDE" >&2
  usage
  exit 2
fi

require_cmd() {
  command -v "$1" >/dev/null 2>&1 || {
    echo "Missing required command: $1" >&2
    exit 1
  }
}

require_cmd docker
require_cmd python3
[[ -x scripts/build.sh ]] || { echo "scripts/build.sh is missing or not executable" >&2; exit 1; }
[[ -x scripts/up.sh ]] || { echo "scripts/up.sh is missing or not executable" >&2; exit 1; }

configured_mode="$(python3 scripts/lib_config.py get deployment.mode)"
mode="$configured_mode"
if [[ -n "$MODE_OVERRIDE" ]]; then
  mode="$MODE_OVERRIDE"
  python3 scripts/lib_config.py set deployment.mode "$mode" >/dev/null
fi

if [[ "$mode" != "robot_only" && "$mode" != "laptop_offload" ]]; then
  echo "Unsupported deployment.mode in config: $mode" >&2
  exit 1
fi

echo "[mustar] mode=$mode"
echo "[mustar] host preflight"

if [[ ! -d /dev/snd ]]; then
  echo "Host audio devices missing: /dev/snd not found (mic/speaker unavailable)" >&2
  exit 1
fi

if [[ ! -e "$VIDEO_PRIMARY" && ! -e "$VIDEO_SECONDARY" && "$ALLOW_NO_VIDEO" != "1" ]]; then
  echo "Host camera devices missing: neither $VIDEO_PRIMARY nor $VIDEO_SECONDARY exists" >&2
  exit 1
fi

echo "- host video devices"
ls -1 /dev/video* 2>/dev/null | sed 's/^/  /' || true
echo "- host audio devices"
ls -1 /dev/snd 2>/dev/null | sed 's/^/  /' || true

echo "[mustar] building images"
scripts/build.sh

echo "[mustar] starting containers"
scripts/up.sh

check_container_av() {
  local service="$1"
  echo "[mustar] verifying $service camera/mic/speaker"

  "${COMPOSE[@]}" ps -q "$service" | rg -q . || {
    echo "Service '$service' is not running" >&2
    exit 1
  }

  if ! "${COMPOSE[@]}" exec -T "$service" test -d /dev/snd; then
    echo "$service: /dev/snd is not mapped" >&2
    exit 1
  fi

  if [[ "$ALLOW_NO_VIDEO" != "1" ]] && ! "${COMPOSE[@]}" exec -T "$service" bash -lc "test -e '$VIDEO_PRIMARY' || test -e '$VIDEO_SECONDARY'"; then
    echo "$service: camera device mapping missing ($VIDEO_PRIMARY / $VIDEO_SECONDARY)" >&2
    exit 1
  fi

  "${COMPOSE[@]}" exec -T "$service" bash -lc 'echo "  audio capture devices:"; arecord -l || true; echo "  audio playback devices:"; aplay -l || true; echo "  video devices:"; ls -1 /dev/video* 2>/dev/null || true'
}

check_container_av robot
if [[ "$mode" == "laptop_offload" ]]; then
  check_container_av laptop
fi

prefetch_models() {
  local service="$1"
  echo "[mustar] prefetching models in $service"
  "${COMPOSE[@]}" exec -T "$service" bash -lc "python3 - <<'PY'
from huggingface_hub import snapshot_download
import whisper

print('prefetch: whisper base')
whisper.load_model('base')
print('prefetch: cardiffnlp/twitter-roberta-base-sentiment-latest')
snapshot_download(repo_id='cardiffnlp/twitter-roberta-base-sentiment-latest')
print('prefetch complete')
PY"
}

prefetch_models robot
if [[ "$mode" == "laptop_offload" ]]; then
  prefetch_models laptop
fi

echo "[mustar] building ros2_ws (robot)"
"${COMPOSE[@]}" exec -T robot bash -lc "source /opt/ros/humble/setup.bash && cd /workspace/ros2_ws && colcon build --symlink-install"

# Avoid duplicate launch processes from prior runs.
"${COMPOSE[@]}" exec -T robot bash -lc "pkill -f 'ros2 launch emotion_robot_bringup' || true"
"${COMPOSE[@]}" exec -T laptop bash -lc "pkill -f 'ros2 launch emotion_robot_bringup' || true"

if [[ "$mode" == "robot_only" ]]; then
  echo "[mustar] launching robot_only bringup"
  exec "${COMPOSE[@]}" exec robot bash -lc "source /opt/ros/humble/setup.bash && source /workspace/ros2_ws/install/setup.bash && ros2 launch emotion_robot_bringup robot_only.launch.py"
fi

echo "[mustar] launching laptop_inference bringup in background"
"${COMPOSE[@]}" exec -d laptop bash -lc "source /opt/ros/humble/setup.bash && source /workspace/ros2_ws/install/setup.bash && nohup ros2 launch emotion_robot_bringup laptop_inference.launch.py > /workspace/runtime/laptop_inference.log 2>&1"

echo "[mustar] launching robot_endpoint bringup"
echo "[mustar] laptop logs: runtime/laptop_inference.log"
exec "${COMPOSE[@]}" exec robot bash -lc "source /opt/ros/humble/setup.bash && source /workspace/ros2_ws/install/setup.bash && ros2 launch emotion_robot_bringup robot_endpoint.launch.py"
