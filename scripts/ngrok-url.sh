#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

reserved="$(python3 scripts/lib_config.py get ngrok.reserved_tcp_addr)"
mkdir -p runtime

if [[ -n "$reserved" ]]; then
  host="${reserved%%:*}"
  port="${reserved##*:}"
  echo "NGROK_HOST=$host" > runtime/ngrok.env
  echo "NGROK_PORT=$port" >> runtime/ngrok.env
  echo "Using reserved ngrok endpoint: $host:$port"
  exit 0
fi

raw="$(curl -sS http://127.0.0.1:4040/api/tunnels)"
public="$(echo "$raw" | jq -r '.tunnels[] | select(.proto=="tcp") | .public_url' | head -n1)"
if [[ -z "$public" || "$public" == "null" ]]; then
  echo "No tcp tunnel found in ngrok API" >&2
  exit 1
fi
endpoint="${public#tcp://}"
host="${endpoint%%:*}"
port="${endpoint##*:}"
echo "NGROK_HOST=$host" > runtime/ngrok.env
echo "NGROK_PORT=$port" >> runtime/ngrok.env
echo "Ephemeral ngrok endpoint: $host:$port"
