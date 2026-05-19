#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"
rm -rf ros2_ws/build ros2_ws/install ros2_ws/log runtime/ngrok.env
