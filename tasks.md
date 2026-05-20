# Master Tasks by Checklist Point

This is the project-level execution tracker synchronized to current implementation.

## Real-World Blockers Snapshot (May 20, 2026)

- Mustar operations depend on stable SSH access and code sync workflow before runtime checks.
- Ubuntu 18.04 environments often miss Docker Compose v2 plugin; this blocks all `scripts/up.sh` paths until fixed.
- ORBBEC ASTRA camera path is non-UVC and requires USB pass-through troubleshooting, not `/dev/video*` assumptions.
- First-run inference delays are dominated by model download; predownload workflow is now required for reliable demos/tests.
- Laptop offload failures are commonly startup-order issues; laptop inference must be started before robot endpoint.

- Phase details: [tasks_phase1_foundation.md](/home/mohamed/Desktop/Cognitive%20Project/ROS2-Robot-Emotion-Aware-RREA-/tasks_phase1_foundation.md)
- Phase details: [tasks_phase2_modalities.md](/home/mohamed/Desktop/Cognitive%20Project/ROS2-Robot-Emotion-Aware-RREA-/tasks_phase2_modalities.md)
- Phase details: [tasks_phase3_validation_docs.md](/home/mohamed/Desktop/Cognitive%20Project/ROS2-Robot-Emotion-Aware-RREA-/tasks_phase3_validation_docs.md)

Status legend:
- `DONE`: implemented and verified in repo/tests.
- `PARTIAL`: implemented or executed, but acceptance closure is still blocked.
- `TODO`: not complete yet.

## Current Implementation Snapshot (May 19, 2026)

- `DONE`: Required core output topics exist in code path: `/camera/emotion`, `/audio/emotion`, `/speech/text`, `/text/sentiment`, `/emotion/final`, `/robot/response`, `/robot/say`.
- `DONE`: `system.launch.py` exists, plus mode launches for `robot_only` and `laptop_offload`.
- `DONE`: Container audio mapping and audio test flow validated for Linux robot container.
- `DONE`: Vision path supports DeepFace-backed FER with configurable confidence gates and deterministic fallback behavior.
- `DONE`: Audio path supports feature extraction plus profile-driven linear classification, with heuristic fallback guardrails.
- `DONE`: STT backend supports Whisper runtime/model/config path controls with readiness telemetry and safe fallback.
- `PARTIAL`: Phase-3 artifacts contain mixed outcomes: C01/C02/C04/C06/C07 passed, C03 pass-with-risk and still not closure-eligible after latest robot-only rerun (10-minute stability not confirmed), C05 not executed, C08/C09 executed attempts but failed to close, C10 partial local-host row only, C11 partially executed (restart only; network-fault scenario skipped), C13 dry-run not run.

## Owner-Ready Execution Checklist

### Phase 1: Foundation

- [x] `FND-03` Canonical topic contract documented. Owner: `ROS`.
- [x] `FND-05` Config wiring audit documented. Owner: `ROS/PLAT`.
- [x] `FND-06` Launch/runtime wiring done for `stt.enabled/backend/transcript_topic`, `tts.enabled/backend/output_topic`, and audio topic remaps. Owner: `ROS`.
- [x] `FND-07` Reproducible clean build/run validation logs refreshed after latest node additions (`artifacts/phase3/FND-07_logs/*`). Owner: `PLAT`.
- [x] `FND-09` Foundation smoke matrix fully automated for both modes (`local_tcp` pass; `ngrok_tcp` token-gated skip captured). Owner: `QA`.
- [x] `FND-10` Phase-1 evidence sign-off archived (`artifacts/phase3/FND-10_phase1_signoff.md`). Owner: `TL/QA`.

### Phase 2: Modalities and Cognition

- [x] `C2-01..C2-10` Node skeletons and pipeline wiring in place. Owner: `MODALITY`.
- [x] `V-*` Upgrade camera emotion from heuristic to full FER model behavior. Owner: `VISION`.
- [x] `A-*` Upgrade audio emotion from heuristic to feature/model-based classification. Owner: `AUDIO`.
- [x] `S-*` Complete Whisper backend integration and runtime control from config. Owner: `STT`.
- [x] `N-*` Harden sentiment behavior and class mapping validation. Owner: `NLP`.
- [x] `F-*` Validate fusion conflict handling with deterministic test vectors. Owner: `FUSION`.

### Phase 3: Validation and Acceptance

- [ ] `P3-C03` `robot_only` integration baseline remains `Pass with Risk` after latest rerun; 10-minute stability/sign-off still open. Owner: `QA`.
- [x] `P3-C04` `laptop_offload` local TCP baseline captured (`Pass`). Owner: `QA`.
- [x] `P3-C06/P3-C07` Audio/STT/TTS baseline runs captured (`Pass` for current fallback behavior). Owner: `QA`.
- [ ] `P3-C05` ngrok transport validation not executed; evidence remains non-execution notes. Owner: `QA/ROS`.
- [ ] `P3-C08/P3-C09` measurement/stress commands were executed, but acceptance failed due runtime bring-up/permission blockers and no valid baseline metrics. Owner: `PERF`.
- [ ] `P3-C10` hardware compatibility partially documented (local-host probe only; no target hardware matrix closure). Owner: `HW/QA`.
- [ ] `P3-C11` fault-injection is partially executed (container restart done; network drop/restore still skipped), so recovery acceptance remains open. Owner: `QA`.
- [ ] `P3-C12/P3-C13` documentation and presentation are in progress (`C12` pass-with-risk, `C13` dry-run still not run). Owner: `DOCS`.
- [ ] `P3-C14` final acceptance gate remains `No-Go`. Owner: `TL`.

## Checklist Rollup Status

- `Academic requirements`: `PARTIAL`
- `Functional requirements`: `PARTIAL`
- `ROS 2 requirements`: `PARTIAL`
- `Docker requirements`: `PARTIAL`
- `AI/ML requirements`: `PARTIAL`
- `Hardware requirements`: `PARTIAL`
- `Software requirements`: `PARTIAL`
- `Testing requirements`: `PARTIAL`
- `Performance requirements`: `PARTIAL`
- `Documentation requirements`: `PARTIAL`
- `Presentation requirements`: `PARTIAL`
- `MVP`: `PARTIAL`
- `Bonus features`: `TODO`
- `Final acceptance`: `TODO`

## Execution Order

1. Close runtime blockers preventing reproducible bring-up for performance/fault gates (C08/C09/C11 prerequisites).
2. Execute missing remote/ngrok and target-hardware validations (C05/C10).
3. Complete C13 timed dry-run and rerun C14 go/no-go with updated evidence.
