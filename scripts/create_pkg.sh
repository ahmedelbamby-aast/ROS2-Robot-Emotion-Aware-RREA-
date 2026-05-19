#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT/ros2_ws/src"
name="${1:?package name required}"
ros2 pkg create --build-type ament_python "$name"
