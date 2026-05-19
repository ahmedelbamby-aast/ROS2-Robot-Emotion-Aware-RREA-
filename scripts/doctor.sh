#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

echo "[doctor] docker"
docker --version
docker compose version

echo "[doctor] config"
mode="$(python3 scripts/lib_config.py get deployment.mode)"
transport="$(python3 scripts/lib_config.py get gateway.transport)"
backend="$(python3 scripts/lib_config.py get inference.backend)"
echo "mode=$mode transport=$transport backend=$backend"

echo "[doctor] model dir"
test -d models && echo "models/ exists" || { echo "models/ missing"; exit 1; }

echo "[doctor] audio host checks"
if [[ -d /dev/snd ]]; then
  echo "/dev/snd exists"
  ls -1 /dev/snd | sed 's/^/  - /'
else
  echo "/dev/snd missing on host (audio I/O in containers will be unavailable)"
fi

echo "[doctor] ngrok checks"
if [[ "$transport" == "ngrok_tcp" ]]; then
  token_var="$(python3 scripts/lib_config.py get ngrok.authtoken_env)"
  token="${!token_var:-}"
  [[ -n "$token" ]] || { echo "missing $token_var"; exit 1; }
  curl -sSf http://127.0.0.1:4040/api/tunnels >/dev/null && echo "ngrok api reachable" || echo "ngrok api not reachable yet"
fi

echo "[doctor] backend/runtime checks"
has_nvidia=0
has_openvino=0
docker info 2>/dev/null | rg -qi nvidia && has_nvidia=1 || true
if docker images --format '{{.Repository}}:{{.Tag}}' | rg -q 'emotion_robot:openvino'; then
  has_openvino=1
fi

selected="$backend"
if [[ "$backend" == "auto" ]]; then
  if [[ "$has_nvidia" -eq 1 ]]; then
    selected="tensorrt"
  elif [[ "$has_openvino" -eq 1 ]]; then
    selected="openvino"
  else
    selected="cpu"
  fi
  echo "auto backend resolved to: $selected"
fi

if [[ "$backend" == "tensorrt" ]]; then
  [[ "$has_nvidia" -eq 1 ]] || { echo "tensorrt selected but nvidia runtime not detected"; exit 1; }
fi
if [[ "$backend" == "openvino" ]]; then
  [[ "$has_openvino" -eq 1 ]] || { echo "openvino selected but emotion_robot:openvino image is not built"; exit 1; }
fi

echo "[doctor] audio container checks"
for service in robot laptop; do
  cid="$(docker compose -f docker/docker-compose.yml ps -q "$service" 2>/dev/null || true)"
  if [[ -z "$cid" ]]; then
    echo "$service: not running"
    continue
  fi
  if docker compose -f docker/docker-compose.yml exec -T "$service" test -d /dev/snd >/dev/null 2>&1; then
    echo "$service: /dev/snd mapped"
  else
    echo "$service: /dev/snd not mapped"
  fi
done

echo "doctor completed"
