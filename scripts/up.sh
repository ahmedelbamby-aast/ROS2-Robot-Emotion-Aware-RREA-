#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"
COMPOSE_FILE="docker/docker-compose.yml"
COMPOSE=(docker compose -f "$COMPOSE_FILE")
AUDIO_OVERRIDE_FILE="runtime/docker-compose.audio.yml"

mode="$(python3 scripts/lib_config.py get deployment.mode)"
transport="$(python3 scripts/lib_config.py get gateway.transport)"
port="$(python3 scripts/lib_config.py get gateway.port)"
host="$(python3 scripts/lib_config.py get gateway.local_host)"
use_ephemeral="$(python3 scripts/lib_config.py get ngrok.use_ephemeral_tcp)"
token_var="$(python3 scripts/lib_config.py get ngrok.authtoken_env)"

export GATEWAY_PORT="$port"

with_audio=0
if [[ -d /dev/snd ]]; then
  cat > "$AUDIO_OVERRIDE_FILE" <<'YAML'
services:
  robot:
    devices:
      - /dev/snd:/dev/snd
  laptop:
    devices:
      - /dev/snd:/dev/snd
YAML
  with_audio=1
else
  rm -f "$AUDIO_OVERRIDE_FILE"
fi

compose_up=(docker compose -f "$COMPOSE_FILE")
if [[ "$with_audio" -eq 1 ]]; then
  compose_up+=( -f "$AUDIO_OVERRIDE_FILE" )
  echo "Audio mapping enabled: /dev/snd"
else
  echo "Audio mapping skipped: /dev/snd not present on host"
fi

if [[ "$mode" == "robot_only" ]]; then
  "${COMPOSE[@]}" stop laptop ngrok >/dev/null 2>&1 || true
  "${compose_up[@]}" --profile robot up -d robot
  rm -f runtime/ngrok.env
  echo "Started robot_only path. Launch: ros2 launch emotion_robot_bringup robot_only.launch.py"
  exit 0
fi

"${compose_up[@]}" --profile robot --profile laptop up -d robot laptop

if [[ "$transport" == "local_tcp" ]]; then
  "${COMPOSE[@]}" stop ngrok >/dev/null 2>&1 || true
  rm -f runtime/ngrok.env
  echo "Laptop offload local tcp target: $host:$port"
  echo "Set ROBOT_GATEWAY_HOST=$host before robot endpoint launch."
  exit 0
fi

if [[ -z "${!token_var:-}" ]]; then
  echo "Missing required ngrok token env var: $token_var" >&2
  exit 1
fi

export NGROK_AUTHTOKEN="${!token_var}"
"${COMPOSE[@]}" --profile ngrok up -d ngrok

if [[ "$use_ephemeral" == "true" ]]; then
  scripts/ngrok-url.sh
fi
echo "Laptop offload ngrok ready. Launch laptop and robot endpoint launch files."
