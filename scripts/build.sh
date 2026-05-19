#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

backend="$(python3 scripts/lib_config.py get inference.backend)"

docker build -f docker/Dockerfile.base -t emotion_robot_base:latest .
docker compose -f docker/docker-compose.yml build robot laptop

if [[ "$backend" == "openvino" ]]; then
  docker build -f docker/Dockerfile.openvino -t emotion_robot:openvino .
elif [[ "$backend" == "tensorrt" ]]; then
  docker build -f docker/Dockerfile.tensorrt -t emotion_robot:tensorrt .
elif [[ "$backend" == "cpu" ]]; then
  docker build -f docker/Dockerfile.cpu -t emotion_robot:cpu .
fi

echo "Build complete (backend=$backend)"
