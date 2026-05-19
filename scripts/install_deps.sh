#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

python3 -m pip install --user pyyaml
source /opt/ros/humble/setup.bash
cd ros2_ws
rosdep update || true
rosdep install --from-paths src --ignore-src -r -y || true
colcon build
