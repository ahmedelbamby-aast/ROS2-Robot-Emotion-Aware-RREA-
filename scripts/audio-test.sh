#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

service="${1:-robot}"
duration="${2:-3}"

if [[ "$service" != "robot" && "$service" != "laptop" ]]; then
  echo "Usage: scripts/audio-test.sh [robot|laptop] [duration_seconds]" >&2
  exit 1
fi

echo "[audio-test] service=$service duration=${duration}s"

docker compose -f docker/docker-compose.yml ps -q "$service" >/dev/null || {
  echo "service '$service' not found in compose" >&2
  exit 1
}

if ! docker compose -f docker/docker-compose.yml exec -T "$service" test -d /dev/snd; then
  echo "container $service does not have /dev/snd mapped" >&2
  echo "Run scripts/up.sh on a Linux host with /dev/snd available." >&2
  exit 1
fi

echo "[audio-test] capture device list"
docker compose -f docker/docker-compose.yml exec -T "$service" bash -lc "arecord -l || true"

echo "[audio-test] playback device list"
docker compose -f docker/docker-compose.yml exec -T "$service" bash -lc "aplay -l || true"

echo "[audio-test] recording /tmp/mic_test.wav"
docker compose -f docker/docker-compose.yml exec -T "$service" bash -lc "arecord -q -d $duration -f cd -t wav /tmp/mic_test.wav"

echo "[audio-test] playing /tmp/mic_test.wav"
docker compose -f docker/docker-compose.yml exec -T "$service" bash -lc "aplay -q /tmp/mic_test.wav"

echo "[audio-test] success"
