#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

ART_DIR="artifacts/phase3"
LOG_DIR="$ART_DIR/FND-09_logs"
MATRIX_FILE="$ART_DIR/FND-09_smoke_matrix.md"

mkdir -p "$LOG_DIR"
mkdir -p "$ART_DIR"

STAMP="$(date -Iseconds)"

run_cmd() {
  local log_file="$1"
  shift
  {
    echo ""
    echo "## COMMAND"
    printf '%q ' "$@"
    echo ""
    echo "## START $(date -Iseconds)"
    "$@"
    local rc=$?
    echo "## EXIT_CODE $rc"
    echo "## END $(date -Iseconds)"
    return $rc
  } >>"$log_file" 2>&1
}

check_prereqs() {
  local ok=0
  if command -v docker >/dev/null 2>&1 && docker compose version >/dev/null 2>&1; then
    ok=1
  fi
  echo "$ok"
}

append_matrix_row() {
  local mode="$1"
  local transport="$2"
  local expected="$3"
  local result="$4"
  local notes="$5"
  local log_rel="$6"
  printf '| %s | %s | %s | %s | %s | %s |\n' \
    "$mode" "$transport" "$expected" "$result" "$notes" "$log_rel" >>"$MATRIX_FILE"
}

setup_matrix_doc() {
  cat >"$MATRIX_FILE" <<DOC
# FND-09 Foundation Smoke Matrix

Generated: $STAMP

| deployment.mode | gateway.transport | Checks | Result | Notes | Log |
|---|---|---|---|---|---|
DOC
}

run_case() {
  local mode="$1"
  local transport="$2"
  local expected="$3"
  local label="${mode}__${transport}"
  local log_file="$LOG_DIR/${label}.log"
  local rel_log="artifacts/phase3/FND-09_logs/${label}.log"

  : >"$log_file"

  if [[ "$(check_prereqs)" != "1" ]]; then
    append_matrix_row "$mode" "$transport" "$expected" "SKIP" "docker/compose unavailable" "$rel_log"
    echo "docker/compose unavailable" >>"$log_file"
    return 0
  fi

  if [[ "$transport" == "ngrok_tcp" ]]; then
    local token_var
    token_var="$(python3 scripts/lib_config.py get ngrok.authtoken_env)"
    if [[ -z "${!token_var:-}" ]]; then
      append_matrix_row "$mode" "$transport" "$expected" "SKIP" "missing ngrok token env var: $token_var" "$rel_log"
      echo "missing ngrok token env var: $token_var" >>"$log_file"
      return 0
    fi
  fi

  local rc=0

  run_cmd "$log_file" scripts/config.sh set deployment.mode "$mode" || rc=1
  run_cmd "$log_file" scripts/config.sh set gateway.transport "$transport" || rc=1
  run_cmd "$log_file" scripts/up.sh || rc=1
  run_cmd "$log_file" scripts/doctor.sh --acceptance-log "$LOG_DIR/${label}.doctor.acceptance.log" || rc=1
  run_cmd "$log_file" docker compose -f docker/docker-compose.yml ps || rc=1

  if [[ $rc -eq 0 ]]; then
    append_matrix_row "$mode" "$transport" "$expected" "PASS" "all smoke commands exited 0" "$rel_log"
  else
    append_matrix_row "$mode" "$transport" "$expected" "FAIL" "see command exit codes in log" "$rel_log"
  fi
}

setup_matrix_doc

run_case "robot_only" "local_tcp" "config set + up + doctor + compose ps"
run_case "laptop_offload" "local_tcp" "config set + up + doctor + compose ps"
run_case "laptop_offload" "ngrok_tcp" "config set + up + doctor + compose ps (ngrok token required)"

echo "" >>"$MATRIX_FILE"
echo "Notes:" >>"$MATRIX_FILE"
echo "- This script records executed command evidence only; it does not claim unavailable hardware or network paths." >>"$MATRIX_FILE"

echo "FND-09 smoke matrix written: $MATRIX_FILE"
