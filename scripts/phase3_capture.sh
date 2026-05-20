#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

ART_DIR="artifacts/phase3"
mkdir -p "$ART_DIR"

C08_CSV="$ART_DIR/P3-C08_perf_baseline.csv"
C09_TRACE="$ART_DIR/P3-C09_resource_trace.csv"
C09_MD="$ART_DIR/P3-C09_stress_results.md"
C10_MD="$ART_DIR/P3-C10_hw_matrix.md"
C11_MD="$ART_DIR/P3-C11_fault_recovery.md"
C11_TIMELINE="$ART_DIR/P3-C11_timeline.txt"

SAMPLES="${P3_SAMPLES:-5}"
SLEEP_SEC="${P3_SAMPLE_SLEEP_SEC:-2}"
STRESS_CMD="${P3_STRESS_CMD:-}"

run_stats_samples() {
  local out_csv="$1"
  local phase="$2"
  local services=(robot laptop ngrok)

  if ! command -v docker >/dev/null 2>&1 || ! docker compose version >/dev/null 2>&1; then
    return 1
  fi

  if [[ ! -f "$out_csv" ]]; then
    echo "timestamp,phase,service,container,cpu_perc,mem_usage,mem_perc,net_io,block_io,pids" >"$out_csv"
  fi

  local i=1
  while [[ $i -le $SAMPLES ]]; do
    local ts
    ts="$(date -Iseconds)"
    local service
    for service in "${services[@]}"; do
      local cid
      cid="$(docker compose -f docker/docker-compose.yml ps -q "$service" 2>/dev/null || true)"
      if [[ -z "$cid" ]]; then
        echo "$ts,$phase,$service,not-running,,,,,," >>"$out_csv"
        continue
      fi
      local line
      line="$(docker stats --no-stream --format '{{.Name}},{{.CPUPerc}},{{.MemUsage}},{{.MemPerc}},{{.NetIO}},{{.BlockIO}},{{.PIDs}}' "$cid" 2>/dev/null || true)"
      if [[ -n "$line" ]]; then
        echo "$ts,$phase,$service,$line" >>"$out_csv"
      else
        echo "$ts,$phase,$service,$cid,stats-unavailable,,,,," >>"$out_csv"
      fi
    done
    i=$((i + 1))
    sleep "$SLEEP_SEC"
  done

  return 0
}

capture_c08() {
  local modes=(robot_only laptop_offload)
  : >"$C08_CSV"
  echo "timestamp,phase,service,container,cpu_perc,mem_usage,mem_perc,net_io,block_io,pids" >"$C08_CSV"

  local mode
  for mode in "${modes[@]}"; do
    scripts/config.sh set deployment.mode "$mode"
    scripts/config.sh set gateway.transport local_tcp
    if ! scripts/up.sh >/dev/null 2>&1; then
      echo "$(date -Iseconds),$mode,setup,error,up-failed,,,,," >>"$C08_CSV"
      continue
    fi
    run_stats_samples "$C08_CSV" "P3-C08:$mode" || {
      echo "$(date -Iseconds),$mode,setup,error,docker-unavailable,,,,," >>"$C08_CSV"
      return 1
    }
  done
  return 0
}

capture_c09() {
  cat >"$C09_MD" <<DOC
# P3-C09 Stress Results

Last updated: $(date -Iseconds)

## Execution Summary
DOC

  if [[ -z "$STRESS_CMD" ]]; then
    cat >>"$C09_MD" <<DOC
- Status: SKIP (no stress command provided)
- Reason: set environment variable \`P3_STRESS_CMD\` to run a local stress command.
- Resource observation still captured in \`$C09_TRACE\`.
DOC
  else
    {
      echo "- Status: EXECUTED"
      echo "- Stress command: \`$STRESS_CMD\`"
    } >>"$C09_MD"

    if bash -lc "$STRESS_CMD" >>"$C09_MD" 2>&1; then
      echo "- Stress command exit: 0" >>"$C09_MD"
    else
      echo "- Stress command exit: non-zero" >>"$C09_MD"
    fi
  fi

  : >"$C09_TRACE"
  echo "timestamp,phase,service,container,cpu_perc,mem_usage,mem_perc,net_io,block_io,pids" >"$C09_TRACE"
  if run_stats_samples "$C09_TRACE" "P3-C09:observation"; then
    echo "- Resource trace capture: complete" >>"$C09_MD"
  else
    echo "- Resource trace capture: skipped (docker unavailable)" >>"$C09_MD"
  fi
}

capture_c10() {
  local ts
  ts="$(date -Iseconds)"

  local os_name="unknown"
  if [[ -r /etc/os-release ]]; then
    os_name="$(. /etc/os-release && echo "${PRETTY_NAME:-unknown}")"
  fi

  local ros2_ver="not-installed"
  if command -v ros2 >/dev/null 2>&1; then
    ros2_ver="$(ros2 --version 2>/dev/null | tr '\n' ' ' | sed 's/[[:space:]]\+$//' || true)"
    if [[ -z "$ros2_ver" ]]; then
      ros2_ver="installed"
    fi
  fi

  local audio="missing"
  [[ -d /dev/snd ]] && audio="present"

  local camera="unknown"
  if command -v v4l2-ctl >/dev/null 2>&1; then
    if v4l2-ctl --list-devices >/tmp/p3_c10_v4l2.txt 2>/dev/null && [[ -s /tmp/p3_c10_v4l2.txt ]]; then
      camera="present"
    else
      camera="missing"
    fi
  fi

  cat >"$C10_MD" <<DOC
# P3-C10 Hardware Matrix

Last updated: $ts

| Platform | OS | ROS 2 | Audio I/O | Camera | Network Mode | Result | Notes |
|---|---|---|---|---|---|---|---|
| local-host | $os_name | $ros2_ver | $audio | $camera | local_tcp | Partial | Local environment probe only; no external robot/laptop hardware claim. |
DOC
}

capture_c11() {
  local ts
  ts="$(date -Iseconds)"

  cat >"$C11_MD" <<DOC
# P3-C11 Fault Injection and Recovery

Last updated: $ts

## Scenarios
DOC

  : >"$C11_TIMELINE"

  if ! command -v docker >/dev/null 2>&1 || ! docker compose version >/dev/null 2>&1; then
    cat >>"$C11_MD" <<DOC
- Container restart fault: SKIP (docker unavailable)
- Network drop/restore fault: SKIP (requires controlled remote/network setup)
DOC
    echo "$ts SKIP docker unavailable" >>"$C11_TIMELINE"
    return 0
  fi

  local robot_cid
  robot_cid="$(docker compose -f docker/docker-compose.yml ps -q robot 2>/dev/null || true)"
  if [[ -z "$robot_cid" ]]; then
    cat >>"$C11_MD" <<DOC
- Container restart fault: SKIP (robot service not running)
DOC
    echo "$(date -Iseconds) SKIP robot service not running" >>"$C11_TIMELINE"
  else
    echo "$(date -Iseconds) restart robot begin" >>"$C11_TIMELINE"
    if docker compose -f docker/docker-compose.yml restart robot >/dev/null 2>&1; then
      sleep 3
      local state
      state="$(docker inspect -f '{{.State.Status}}' "$robot_cid" 2>/dev/null || echo unknown)"
      echo "$(date -Iseconds) restart robot end state=$state" >>"$C11_TIMELINE"
      cat >>"$C11_MD" <<DOC
- Container restart fault: EXECUTED
  - Action: \`docker compose restart robot\`
  - Post-check state: $state
DOC
    else
      echo "$(date -Iseconds) restart robot failed" >>"$C11_TIMELINE"
      cat >>"$C11_MD" <<DOC
- Container restart fault: FAIL (restart command returned non-zero)
DOC
    fi
  fi

  cat >>"$C11_MD" <<DOC
- Network drop/restore fault: SKIP (not automated here to avoid fabricating remote/ngrok path behavior)
DOC
}

capture_c08 || true
capture_c09
capture_c10
capture_c11

echo "Phase3 capture artifacts updated:"
echo "- $C08_CSV"
echo "- $C09_MD"
echo "- $C09_TRACE"
echo "- $C10_MD"
echo "- $C11_MD"
echo "- $C11_TIMELINE"
