#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

usage() {
  echo "Usage:"
  echo "  scripts/config.sh set deployment.mode robot_only|laptop_offload"
  echo "  scripts/config.sh set gateway.transport local_tcp|ngrok_tcp"
  echo "  scripts/config.sh set gateway.local_host 192.168.1.100"
  echo "  scripts/config.sh set gateway.port 8765"
  echo "  scripts/config.sh set ngrok.reserved_tcp_addr host:port"
  echo "  scripts/config.sh set inference.backend auto|openvino|tensorrt|cpu"
  echo "  scripts/config.sh get key"
}

cmd="${1:-}"
if [[ "$cmd" == "set" ]]; then
  [[ $# -eq 3 ]] || { usage; exit 1; }
  python3 scripts/lib_config.py set "$2" "$3"
elif [[ "$cmd" == "get" ]]; then
  [[ $# -eq 2 ]] || { usage; exit 1; }
  python3 scripts/lib_config.py get "$2"
else
  usage
  exit 1
fi
