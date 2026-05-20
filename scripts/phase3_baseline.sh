#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

ART="artifacts/phase3"
LOGDIR="$ART/P3-C07_logs"
mkdir -p "$ART"
mkdir -p "$LOGDIR"

run_capture() {
  local out="$1"
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
  } >> "$out" 2>&1
}

echo "[phase3] C01 environment smoke" | tee "$ART/P3-C01_env_smoke.md"
{
  echo "date=$(date -Iseconds)"
  echo "pwd=$PWD"
  echo
  docker --version
  docker compose version
  python3 --version
} >> "$ART/P3-C01_env_smoke.md" 2>&1

run_capture "$ART/P3-C01_env_smoke.md" scripts/build.sh
run_capture "$ART/P3-C01_env_smoke.md" scripts/up.sh
run_capture "$ART/P3-C01_env_smoke.md" scripts/doctor.sh --acceptance-log "$ART/P3-C01_doctor_acceptance.log"
run_capture "$ART/P3-C01_env_smoke.md" docker compose -f docker/docker-compose.yml ps

cat > "$ART/P3-C03_robot_only.log" <<'EOF'
# P3-C03 Robot-Only Integration Log
status: placeholder

Runbook commands:
1. scripts/config.sh set deployment.mode robot_only
2. scripts/up.sh
3. docker compose -f docker/docker-compose.yml exec -T robot bash -lc "source /opt/ros/humble/setup.bash && source /workspace/ros2_ws/install/setup.bash && ros2 launch emotion_robot_bringup robot_only.launch.py"
4. docker compose -f docker/docker-compose.yml exec -T robot bash -lc "source /opt/ros/humble/setup.bash && source /workspace/ros2_ws/install/setup.bash && ros2 topic list"
5. docker compose -f docker/docker-compose.yml exec -T robot bash -lc "source /opt/ros/humble/setup.bash && source /workspace/ros2_ws/install/setup.bash && ros2 node list"

Acceptance:
- launch has no fatal errors
- required topics visible
- 10-minute stability observation logged
EOF

cat > "$ART/P3-C04_local_tcp.log" <<'EOF'
# P3-C04 Laptop Offload (local_tcp) Integration Log
status: placeholder

Runbook commands:
1. scripts/config.sh set deployment.mode laptop_offload
2. scripts/config.sh set gateway.transport local_tcp
3. scripts/up.sh
4. docker compose -f docker/docker-compose.yml exec -T laptop bash -lc "source /opt/ros/humble/setup.bash && source /workspace/ros2_ws/install/setup.bash && ros2 launch emotion_robot_bringup laptop_inference.launch.py"
5. docker compose -f docker/docker-compose.yml exec -T robot bash -lc "source /opt/ros/humble/setup.bash && source /workspace/ros2_ws/install/setup.bash && ros2 launch emotion_robot_bringup robot_endpoint.launch.py"

Acceptance:
- robot endpoint connects to laptop gateway
- no repeated disconnects in 10-minute window
- /emotion/final and /robot/response remain active
EOF

cat > "$ART/P3-C07_stt_tts_matrix.md" <<'EOF'
# P3-C07 STT/TTS Runtime Matrix

| stt.enabled | tts.enabled | Expected behavior | Result | Notes | Log |
|---|---|---|---|---|---|
| true | true | STT publishes /speech/text, TTS consumes /robot/say | pending |  | artifacts/phase3/P3-C07_logs/stt1_tts1.log |
| true | false | STT active, TTS disabled/no speech output | pending |  | artifacts/phase3/P3-C07_logs/stt1_tts0.log |
| false | true | STT disabled, TTS still speaks /robot/say | pending |  | artifacts/phase3/P3-C07_logs/stt0_tts1.log |
| false | false | neither STT nor TTS active output path | pending |  | artifacts/phase3/P3-C07_logs/stt0_tts0.log |

Execution notes:
- For each matrix row, set config keys then restart stack with scripts/up.sh.
- Capture launch logs and topic evidence in the mapped log file.
EOF

for f in stt1_tts1.log stt1_tts0.log stt0_tts1.log stt0_tts0.log; do
  if [[ ! -f "$LOGDIR/$f" ]]; then
    cat > "$LOGDIR/$f" <<'EOF'
# Placeholder log
# Add commands executed, relevant ros2 topic echo/list output, and pass/fail decision.
EOF
  fi
done

echo "[phase3] C02 tests" | tee "$ART/P3-C02_pytest.log"
python3 -m pytest -q tests/test_project_config.py tests/test_lib_config.py tests/test_up_script_modes.py >> "$ART/P3-C02_pytest.log" 2>&1

echo "[phase3] C06 audio test" | tee "$ART/P3-C06_audio_test.log"
scripts/audio-test.sh robot 3 >> "$ART/P3-C06_audio_test.log" 2>&1

echo "phase3 baseline completed"
