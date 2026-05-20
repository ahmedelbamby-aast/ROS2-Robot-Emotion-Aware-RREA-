# Phase 3 Tasks: Validation, Documentation, and Final Acceptance

## Runtime Issues Seen in Practice (May 20, 2026)

- Compose v2 plugin absence remains a recurrent setup blocker on older Ubuntu hosts.
- ngrok validations remain token-gated and should be marked blocked when `NGROK_AUTHTOKEN` is unavailable.
- Camera validation must branch by source mode (`uvc` vs `astra`) to avoid false negatives.
- Offload validation failures are frequently caused by launch order and host/port mismatch.

## Scope
Phase 3 covers:

- End-to-end testing and regression validation
- Performance measurement and tuning validation
- Hardware validation across supported deployment modes
- Documentation completion and verification
- Presentation/demo packaging
- Final acceptance and release-readiness sign-off

## Working Rules

- Do not revert or overwrite unrelated edits from other collaborators.
- Run all checks from a clean runtime state (`scripts/down.sh` then `scripts/up.sh` as needed).
- Record every executed command and result in evidence artifacts.
- Any failed acceptance criterion blocks sign-off until resolved or risk-accepted.

## Checklist-Point Mapping

| Checklist ID | Area | Goal | Primary Owner | Dependencies | Evidence Artifact(s) |
|---|---|---|---|---|---|
| P3-C01 | Test Baseline | Validate reproducible environment and core smoke run | QA/Infra | Docker, ROS 2 setup | `artifacts/phase3/P3-C01_env_smoke.md` |
| P3-C02 | Unit/Config Tests | Ensure config and script logic pass regression checks | QA | Python/pytest | `artifacts/phase3/P3-C02_pytest.log` |
| P3-C03 | Integration Pipeline | Validate robot_only launch and data flow | QA/ROS | Build complete | `artifacts/phase3/P3-C03_robot_only.log` |
| P3-C04 | Offload Local TCP | Validate laptop_offload local gateway path | QA/ROS | P3-C03 | `artifacts/phase3/P3-C04_local_tcp.log` |
| P3-C05 | Offload ngrok TCP | Validate remote tunnel flow and endpoint connectivity | QA/ROS | ngrok token | `artifacts/phase3/P3-C05_ngrok.log`, `runtime/ngrok.env` snapshot |
| P3-C06 | Audio I/O Validation | Confirm capture/playback and topic behavior in containers | QA/Audio | Audio device mapped | `artifacts/phase3/P3-C06_audio_test.log` |
| P3-C07 | STT/TTS Runtime Check | Validate enabled/disabled behavior and topic outputs | QA/Audio | P3-C06 | `artifacts/phase3/P3-C07_stt_tts_matrix.md` |
| P3-C08 | Performance Baseline | Capture latency, throughput, and resource usage baseline | Perf | Stable run | `artifacts/phase3/P3-C08_perf_baseline.csv` |
| P3-C09 | Performance Limits | Stress test sustained run and identify bottlenecks | Perf | P3-C08 | `artifacts/phase3/P3-C09_stress_results.md` |
| P3-C10 | Hardware Validation | Verify behavior on target robot host and laptop host | HW/QA | Access to hardware | `artifacts/phase3/P3-C10_hw_matrix.md` |
| P3-C11 | Fault Injection | Validate graceful recovery from expected failures | QA/ROS | P3-C03..P3-C05 | `artifacts/phase3/P3-C11_fault_recovery.md` |
| P3-C12 | Docs Completeness | Ensure install/run/troubleshooting docs are accurate | Docs | All prior validation | `artifacts/phase3/P3-C12_docs_review.md` |
| P3-C13 | Presentation Package | Prepare demo script, slides, and evidence bundle | PM/Tech Lead | P3-C01..P3-C12 | `artifacts/phase3/P3-C13_demo_script.md`, `artifacts/phase3/P3-C13_slide_checklist.md` |
| P3-C14 | Final Acceptance | Formal go/no-go decision with open-risk register | Lead/Stakeholders | All checklist points | `artifacts/phase3/P3-C14_acceptance_signoff.md` |

## Current Artifact Reality (May 19, 2026)

- `Closed evidence`: C01, C02, C04, C06, C07 are pass-closed with execution artifacts.
- `Pass with Risk`: C03 and C12 are executed but still have acceptance gaps.
- `Executed but not closed`: C08/C09/C10/C11 show recorded attempts/partials, but do not meet acceptance criteria.
- `Blocked/Not closed`: C05 ngrok validation is blocked by missing `NGROK_AUTHTOKEN`; C13 has a timed artifact walkthrough run but does not satisfy the 10-15 minute dry-run criterion.
- `Executed as non-closing attempts`: C08/C09 were run but did not produce acceptance-grade baseline/stress outputs.
- `Gate decision`: C14 remains `No-Go` based on unresolved acceptance blockers and missing stakeholder sign-off.

## Detailed Tasks

## P3-C01 Environment Baseline and Smoke Validation

- [x] Capture baseline versions and environment fingerprint (`docker`, `docker compose`, `python`, ROS distro).
- [x] Run `scripts/build.sh`, `scripts/up.sh`, `scripts/doctor.sh`.
- [x] Verify expected containers are up for current deployment mode.

Acceptance criteria:

- All required tooling versions are documented.
- Build/startup exits with code `0`.
- `doctor` reports no blocking issues.

Evidence artifacts:

- `artifacts/phase3/P3-C01_env_smoke.md`
- `artifacts/phase3/P3-C01_compose_ps.txt`
- `artifacts/phase3/P3-C01_doctor_acceptance.log`

Automation note:

- `scripts/phase3_baseline.sh` now auto-generates C01 baseline evidence and acceptance-formatted doctor output.

## P3-C02 Unit and Config Regression Tests

- [x] Run `python3 -m pytest -q tests/test_project_config.py tests/test_lib_config.py tests/test_up_script_modes.py`.
- [x] Run full `python3 -m pytest -q tests`.
- [ ] Log failed tests (if any), root cause, and retest results.

Acceptance criteria:

- Targeted config/mode tests all pass.
- No untriaged failures in `tests` suite.

Evidence artifacts:

- `artifacts/phase3/P3-C02_pytest.log`
- `artifacts/phase3/P3-C02_failures_triage.md` (only if failures occur)

## P3-C03 Integration: Robot-Only Pipeline

- [x] Set `deployment.mode=robot_only`.
- [x] Launch `robot_only.launch.py` in container.
- [x] Validate expected ROS topics/nodes and startup logs.
- [ ] Capture/confirm 10-minute stability observation window in artifact.

Acceptance criteria:

- Launch completes without fatal errors.
- Core topics publish at expected cadence.
- No crash/restart loop in a 10-minute observation window.

Evidence artifacts:

- `artifacts/phase3/P3-C03_robot_only.log`
- `artifacts/phase3/P3-C03_topics_snapshot.txt`

## P3-C04 Integration: Laptop Offload via Local TCP

- [x] Set `deployment.mode=laptop_offload`, `gateway.transport=local_tcp`.
- [x] Launch laptop inference endpoint.
- [x] Launch robot endpoint with `ROBOT_GATEWAY_HOST`.
- [x] Verify connection and inference loop continuity.
- [ ] Capture/confirm 10-minute disconnect-free run in artifact.

Acceptance criteria:

- Robot endpoint connects to gateway successfully.
- No repeated disconnects over 10-minute run.
- Emotion output path remains active.

Evidence artifacts:

- `artifacts/phase3/P3-C04_local_tcp.log`
- `artifacts/phase3/P3-C04_connection_events.txt`

## P3-C05 Integration: Laptop Offload via ngrok TCP

Current status note:
- `Not executed`: artifact files exist and explicitly record non-execution.

- [ ] Set `gateway.transport=ngrok_tcp`.
- [ ] Export `NGROK_AUTHTOKEN` and run `scripts/up.sh`.
- [ ] Generate and validate tunnel endpoint.
- [ ] Verify robot-host connection through tunnel.

Acceptance criteria:

- Valid tunnel address generated and consumed by robot endpoint.
- End-to-end path works for at least one full inference cycle.
- Any network jitter observed is recorded with severity.

Evidence artifacts:

- `artifacts/phase3/P3-C05_ngrok.log`
- `artifacts/phase3/P3-C05_tunnel_details.txt`

## P3-C06 Audio I/O Hardware Path Validation

- [ ] Run `scripts/audio-test.sh robot 3` and `scripts/audio-test.sh laptop 3`.
- [x] Confirm container sound device mapping and playback capture behavior.
- [ ] Validate `audio.input_topic` and downstream emotion topic activity.

Acceptance criteria:

- Audio capture and playback succeed in both required containers.
- No persistent ALSA/Pulse errors that block runtime function.

Evidence artifacts:

- `artifacts/phase3/P3-C06_audio_test.log`
- `artifacts/phase3/P3-C06_audio_topics.txt`

## P3-C07 STT/TTS Runtime Matrix Validation

- [x] Validate matrix of scenarios: `stt.enabled` true/false, `tts.enabled` true/false.
- [x] Confirm behavior aligns with current documented wiring limitations.
- [x] Record topic-level and log-level outputs per scenario.

Acceptance criteria:

- Each matrix cell has pass/fail plus notes.
- Known partial wiring behavior is documented without ambiguity.

Evidence artifacts:

- `artifacts/phase3/P3-C07_stt_tts_matrix.md`
- `artifacts/phase3/P3-C07_logs/` (folder of per-run logs)

## P3-C08 Performance Baseline

Current status note:
- `Executed and re-tested locally (2026-05-19) but failed to close`: 3 repeated runs were captured in `robot_only` and `laptop_offload`; resource metrics exist, but runs are not reproducible and no latency/throughput baseline is captured.

- [x] Define measurement protocol scaffold and CSV headers.
- [x] Attempt baseline collection in `robot_only` and `laptop_offload` local TCP modes.
- [ ] Capture valid latency/CPU/memory metrics from running services.

Acceptance criteria:

- Baseline metrics captured for both modes.
- Data is reproducible across 3 repeated runs (within agreed variance band).

Evidence artifacts:

- `artifacts/phase3/P3-C08_perf_baseline.csv`
- `artifacts/phase3/P3-C08_method.md`

## P3-C09 Performance Stress and Limits

Current status note:
- `Executed and re-tested locally (2026-05-19) but failed to close`: sustained stress probes and resource traces were captured for 3 runs without Docker permission issues, but workload activation was inconsistent and stress command exits were non-zero, so stress-limit characterization is not acceptance-grade.

- [x] Run stress probe command and capture result/log output.
- [x] Record observed service states during attempt.
- [ ] Execute sustained stress run on a healthy runtime and identify degradation point.

Acceptance criteria:

- No catastrophic failures under nominal sustained load.
- Bottlenecks ranked with actionable mitigation items.

Evidence artifacts:

- `artifacts/phase3/P3-C09_stress_results.md`
- `artifacts/phase3/P3-C09_resource_trace.csv`

## P3-C10 Hardware Compatibility Matrix

Current status note:
- `Partial`: one local-host probe row exists; target robot/laptop validation set is not complete.

- [x] Record local-host probe row.
- [ ] Validate on target robot machine and developer laptop host.
- [ ] Record OS, kernel, driver/audio stack, and device IDs.
- [ ] Execute minimal validation subset (P3-C01, C03/C04, C06) per hardware profile.

Acceptance criteria:

- Compatibility matrix completed for each tested hardware profile.
- Any hardware-specific workaround is documented and reproducible.

Evidence artifacts:

- `artifacts/phase3/P3-C10_hw_matrix.md`
- `artifacts/phase3/P3-C10_workarounds.md`

## P3-C11 Fault Injection and Recovery

Current status note:
- `Partial`: container restart fault scenario is executed; network drop/restore scenario is still skipped, so recovery coverage is incomplete.

- [x] Record scenario disposition for container restart fault.
- [x] Record scenario disposition for network drop/restore fault.
- [ ] Execute both faults on active runtime and measure recovery behavior.

Acceptance criteria:

- Recovery behavior documented with recovery time and manual steps.
- No silent failure mode without observability signal.

Evidence artifacts:

- `artifacts/phase3/P3-C11_fault_recovery.md`
- `artifacts/phase3/P3-C11_timeline.txt`

## P3-C12 Documentation Completion and Verification

Current status note:
- `Pass with Risk`: docs are broadly aligned to executed local evidence, but command-evidence closure is incomplete.

- [x] Verify `README.md`, `INSTALLATION.md`, `QUICKSTART.md` against actual commands.
- [ ] Add troubleshooting entries for observed Phase 3 issues where still missing.
- [ ] Verify Linux and Windows command parity where claimed.

Acceptance criteria:

- All documented commands tested at least once during Phase 3.
- No stale or contradictory instruction remains.

Evidence artifacts:

- `artifacts/phase3/P3-C12_docs_review.md`
- `artifacts/phase3/P3-C12_docs_command_checklist.md`

## P3-C13 Presentation and Demo Readiness

Current status note:
- `In Progress`: demo script exists; one timed dry-run artifact walkthrough was executed, but closure criteria are not met yet.

- [x] Prepare a 10-15 minute demo runbook with exact command sequence.
- [ ] Build evidence-backed summary slides (goals, architecture, validation results, risks).
- [x] Conduct one timed dry-run and capture issues.

Acceptance criteria:

- Dry-run completes within allotted time.
- All claims in presentation trace to captured artifacts.

Evidence artifacts:

- `artifacts/phase3/P3-C13_demo_script.md`
- `artifacts/phase3/P3-C13_slide_checklist.md`
- `artifacts/phase3/P3-C13_dry_run_notes.md`

## P3-C14 Final Acceptance and Sign-Off

Current status note:
- `No-Go`: unresolved checklist blockers remain (C05, C08, C09, C10, C11 execution closure, C13 dry-run).

- [x] Compile checklist statuses in one acceptance dashboard.
- [x] Record unresolved risks with owner and due date.
- [ ] Hold go/no-go review with complete evidence closure and capture final stakeholder approvals.

Acceptance criteria:

- Every checklist ID is `Pass`, `Pass with Risk`, or `Fail` with justification.
- Sign-off document includes stakeholders, date, and final release recommendation.

Evidence artifacts:

- `artifacts/phase3/P3-C14_acceptance_signoff.md`
- `artifacts/phase3/P3-C14_risk_register.md`

## Latest Mustar Readiness (May 20, 2026)

- Camera path validated on Mustar using `astra_camera` via `rchomeedu_vision/multi_astra.launch`.
- Confirmed live RGB stream publication on both `/camera_top/rgb/image_raw` and `/camera/rgb/image_raw` at approximately 28-29 Hz.
- Project defaults updated for Mustar ASTRA flow:
  - `vision.source: astra`
  - `vision.input_topic: /camera_top/rgb/image_raw`
  - `vision.astra_bridge_cmd` launches the proven Mustar ROS1 ASTRA stack.
- Added helper script: `scripts/start_mustar_astra_host.sh` for host-side ASTRA bringup and quick verification.
- Microphone readiness validated on Mustar host with non-zero captured signal (`rms=315`, `max=2325`).
- Speaker readiness validated on Mustar host (`aplay` playback successful).

### Status

- Camera: Ready (host-level, real frames confirmed)
- Microphone: Ready (host-level)
- Speaker: Ready (host-level)
- Full dual-mode E2E: pending final model cache completion and integrated runtime validation

