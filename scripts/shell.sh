#!/usr/bin/env bash
set -euo pipefail
service="${1:-robot}"
docker compose -f "$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)/docker/docker-compose.yml" exec "$service" bash
