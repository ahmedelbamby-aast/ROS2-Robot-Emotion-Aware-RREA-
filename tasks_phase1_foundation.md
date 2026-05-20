# Phase 1 Tasks: Foundation and Infrastructure

## Current Operational Constraints (May 20, 2026)

- Enforce Docker Compose v2 plugin requirement across Linux hosts, including Ubuntu 18.04 CLI-only installations.
- Mustar readiness includes SSH connectivity, repo sync, and device preflight before launch.
- Camera prerequisites must distinguish UVC (`/dev/video*`) from ASTRA non-UVC (`/dev/bus/usb`) paths.

## Current Status Sync (May 19, 2026)

- `FND-03`: completed documentation artifact exists in [FOUNDATION_TOPIC_CONTRACT.md](/home/mohamed/Desktop/Cognitive%20Project/ROS2-Robot-Emotion-Aware-RREA-/FOUNDATION_TOPIC_CONTRACT.md).
- `FND-05`: completed documentation artifact exists in [CONFIG_WIRING_AUDIT.md](/home/mohamed/Desktop/Cognitive%20Project/ROS2-Robot-Emotion-Aware-RREA-/CONFIG_WIRING_AUDIT.md).
- `FND-06`: still open; config keys are not fully bridged into all runtime params.
- `FND-07`: completed; fresh reproducibility evidence refreshed after latest node additions in `artifacts/phase3/FND-07_logs/`.
- `FND-08`: partially complete in docs, needs explicit final host-matrix evidence.
- `FND-09`: completed; automated smoke matrix evidence archived in `artifacts/phase3/FND-09_smoke_matrix.md`.
- `FND-10`: completed; phase closure sign-off archived in `artifacts/phase3/FND-10_phase1_signoff.md`.

## Scope Boundaries
This phase covers only foundational and infrastructure work:
- Repository hygiene and project standards
- ROS topic contract definition and validation hooks
- Launch architecture cleanup and parameter plumbing
- Config wiring from `config/project.yaml` into launch/runtime
- Docker/runtime prerequisites and environment readiness

Out of scope for Phase 1:
- Model quality tuning
- Emotion classifier behavior changes
- UX/product behavior changes
- Feature-level logic in emotion response pipeline

## Suggested Owners (Role-Based)
- **Tech Lead / Architect (TL):** cross-cutting decisions, approvals, sign-off
- **ROS Engineer (ROS):** launch files, topic contracts, ROS parameter handling
- **Platform Engineer (PLAT):** Docker, compose/runtime scripts, env prerequisites
- **QA/Automation Engineer (QA):** validation checklist, smoke tests, CI hooks
- **Docs Maintainer (DOCS):** runbooks, architecture notes, contributor docs

## Checklist-Point Mapping (Phase Gate)
Use this table as the phase gate. Every point must be `Done` with evidence.

| ID | Checklist Point | Mapped Workstream | Primary Owner | Status |
|---|---|---|---|---|
| FND-01 | Repo standards baseline is defined and enforced | A. Repo Hygiene | TL + DOCS | PARTIAL |
| FND-02 | Branch/PR conventions and ownership map are documented | A. Repo Hygiene | TL + DOCS | PARTIAL |
| FND-03 | Canonical ROS topic contract doc exists and is versioned | B. ROS Topic Contract | ROS | DONE |
| FND-04 | Launch files conform to a single architecture pattern | C. Launch Architecture | ROS | PARTIAL |
| FND-05 | All required config keys are wired from project config to runtime | D. Config Wiring | ROS + PLAT | PARTIAL |
| FND-06 | Config validation path fails fast on invalid/missing critical fields | D. Config Wiring | ROS + QA | PARTIAL |
| FND-07 | Docker images and compose targets are reproducible from clean checkout | E. Docker/Runtime Prerequisites | PLAT | DONE |
| FND-08 | Host prerequisites (Linux/Windows) are explicitly documented + testable | E. Docker/Runtime Prerequisites | PLAT + DOCS | PARTIAL |
| FND-09 | Minimal smoke-test matrix for foundation paths is automated | F. Foundation Validation | QA | DONE |
| FND-10 | Phase-1 sign-off checklist evidence is archived in repo | F. Foundation Validation | TL + QA | DONE |

## Phase 1 Execution Checklist (Owner Ready)

- [x] `ROS` Publish canonical topic contract (`FND-03`).
- [x] `ROS/PLAT` Publish config-to-runtime wiring audit (`FND-05`).
- [ ] `ROS` Complete runtime wiring for `stt.*`, `tts.*`, and configurable topic names (`FND-05/FND-06`).
- [ ] `QA` Add negative tests for missing/invalid critical keys with fail-fast output (`FND-06/FND-09`).
- [x] `PLAT` Regenerate clean-checkout build/up/down evidence logs (`FND-07`).
- [ ] `PLAT/DOCS` Finalize Linux+Windows prerequisite matrix with command-level verification outputs (`FND-08`).
- [x] `QA` Execute smoke matrix for `robot_only` and `laptop_offload` with pass/fail table (`FND-09`).
- [x] `TL/QA` Archive phase closure report and sign-off sheet (`FND-10`).

## Workstreams and Concrete Subtasks

## A) Repo Hygiene

### A1. Baseline standards file set
- **Subtasks**
  - Confirm/normalize baseline docs: `README.md`, `QUICKSTART.md`, `INSTALLATION.md`, contribution guidance.
  - Add or update a lightweight ownership map (areas + accountable role).
  - Define canonical script entrypoints (`build`, `up`, `down`, `doctor`, launch wrappers) and deprecate duplicates if any.
- **Acceptance Criteria**
  - New contributor can identify setup, run, and troubleshooting path in under 10 minutes.
  - Ownership map clearly names a role for each top-level subsystem.
  - No conflicting command instructions across core docs.
- **Suggested Owner**: DOCS (driver), TL (approver)
- **Checklist IDs**: FND-01, FND-02

### A2. Repository consistency checks
- **Subtasks**
  - Add/confirm basic lint/test invocation section for config/scripts.
  - Ensure generated artifacts are not tracked unintentionally (validate ignore rules).
  - Add a short “Definition of Done for infra changes” section.
- **Acceptance Criteria**
  - Clean checkout + documented commands succeed on maintained platforms.
  - No accidental generated/build outputs are part of normal commits.
- **Suggested Owner**: TL + QA
- **Checklist IDs**: FND-01

## B) ROS Topic Contract

### B1. Canonical topic contract specification
- **Subtasks**
  - Create a single source-of-truth topic contract doc (topic name, message type, publisher/subscriber ownership, QoS expectation, required/optional).
  - Include currently configured topics from `config/project.yaml` (`audio.input_topic`, `audio.emotion_topic`, `stt.transcript_topic`, `tts.output_topic`).
  - Define naming conventions for any future topics (namespace/prefix guidance).
- **Acceptance Criteria**
  - Every foundation-relevant topic has one declared owner and one declared message type.
  - No ambiguous duplicate names across launch modes.
- **Suggested Owner**: ROS
- **Checklist IDs**: FND-03

### B2. Contract validation hook
- **Subtasks**
  - Add a lightweight validation step (script/test) that checks expected topic keys exist in config and are non-empty.
  - Add a smoke command to inspect active topic graph in each deployment mode.
- **Acceptance Criteria**
  - Validation fails CI/local checks when critical topic fields are missing.
  - Robot-only and laptop-offload both expose expected core topics at runtime.
- **Suggested Owner**: ROS + QA
- **Checklist IDs**: FND-03, FND-09

## C) Launch Architecture

### C1. Launch topology normalization
- **Subtasks**
  - Standardize role of each launch file:
    - `robot_only.launch.py`
    - `laptop_inference.launch.py`
    - `robot_endpoint.launch.py`
    - optional parent orchestrator (`system.launch.py`) as composition-only wrapper.
  - Remove hardcoded assumptions where config-driven behavior is expected.
  - Ensure naming/arguments are consistent across launch files.
- **Acceptance Criteria**
  - Launch entrypoints are unambiguous and map 1:1 to deployment mode responsibilities.
  - Launch arguments/parameters follow one naming convention.
- **Suggested Owner**: ROS
- **Checklist IDs**: FND-04

### C2. Launch observability readiness
- **Subtasks**
  - Ensure each launch path logs mode, transport, and critical endpoints at startup.
  - Add minimal failure messaging for common misconfiguration cases.
- **Acceptance Criteria**
  - Startup logs show enough context to debug wrong mode/transport without code inspection.
- **Suggested Owner**: ROS
- **Checklist IDs**: FND-04, FND-10

## D) Config Wiring

### D1. End-to-end config key wiring audit
- **Subtasks**
  - Build a mapping table: `config/project.yaml` key -> script/launch consumer -> runtime effect.
  - Mark keys as `wired`, `partially wired`, or `not wired`.
  - Prioritize wiring of foundation-critical keys (deployment mode, gateway transport/port/host, audio and STT/TTS topics).
- **Acceptance Criteria**
  - No critical foundation key remains “not wired.”
  - Mapping table is stored in repo and referenced by runbook docs.
- **Suggested Owner**: ROS + PLAT
- **Checklist IDs**: FND-05

### D2. Config schema/guardrails
- **Subtasks**
  - Add strict checks for required keys and allowed values (at minimum for deployment and gateway transport).
  - Fail fast with clear error messages in scripts/entrypoints when config is invalid.
  - Add tests for positive and negative config cases.
- **Acceptance Criteria**
  - Invalid mode/transport values cause deterministic failure with actionable message.
  - Test suite covers required happy path + misconfiguration path.
- **Suggested Owner**: QA (tests) + ROS/PLAT (implementation)
- **Checklist IDs**: FND-06, FND-09

## E) Docker and Runtime Prerequisites

### E1. Build/runtime reproducibility
- **Subtasks**
  - Verify all documented Dockerfiles/compose flows build from clean state.
  - Document expected build targets for robot/laptop roles and backend variants.
  - Verify runtime scripts (`build`, `up`, `doctor`, launch wrappers) are aligned with compose services.
- **Acceptance Criteria**
  - Fresh machine (with prerequisites) can build and bring up required services using documented commands.
  - No undocumented manual step is required for default local mode.
- **Suggested Owner**: PLAT
- **Checklist IDs**: FND-07

### E2. Host prerequisite matrix
- **Subtasks**
  - Define minimum host requirements (OS, Docker/Compose versions, GPU/runtime assumptions, audio device requirements).
  - Add Linux and Windows prerequisite checks (or manual checklist) and expected outputs.
  - Document environment variables needed by transport mode (e.g., ngrok token env var).
- **Acceptance Criteria**
  - Operators can self-verify readiness before `up` using one checklist/doctor flow.
  - Prerequisite gaps are reported before runtime launch failures.
- **Suggested Owner**: PLAT + DOCS
- **Checklist IDs**: FND-08

## F) Foundation Validation and Sign-off

### F1. Smoke-test matrix for foundation paths
- **Subtasks**
  - Define minimum matrix:
    - `robot_only` + `local_tcp`
    - `laptop_offload` + `local_tcp`
    - `laptop_offload` + `ngrok_tcp` (if token/env present)
  - Validate config parsing, launch startup, topic visibility, and script health checks.
- **Acceptance Criteria**
  - Matrix is executable via documented commands and produces pass/fail outcomes.
  - Failures provide direct pointer to config, launch, or runtime layer.
- **Suggested Owner**: QA
- **Checklist IDs**: FND-09

### F2. Phase evidence and closure
- **Subtasks**
  - Attach links/paths to evidence artifacts (test logs, doctor output, screenshots/text dumps).
  - Complete gate table status updates with approver initials/date.
  - Publish Phase 1 closure note and known deferred items for Phase 2.
- **Acceptance Criteria**
  - Every checklist ID has explicit evidence and final status.
  - Deferred work list is finite, scoped, and non-blocking for foundation completion.
- **Suggested Owner**: TL + QA
- **Checklist IDs**: FND-10

## Definition of Done (Phase 1)
Phase 1 is complete only when:
- All checklist points `FND-01` through `FND-10` are marked done with evidence.
- Robot-only and laptop-offload foundation flows start reliably through documented commands.
- Topic/config/launch contracts are documented, validated, and owned.
- Docker/runtime prerequisites are reproducible on target host setups.

## Risks and Early Mitigations
- **Risk:** Config keys exist but are not consumed uniformly across scripts/launch files.
  - **Mitigation:** Maintain and review the config wiring table as a required PR artifact.
- **Risk:** Mode-specific runtime drift (`robot_only` vs `laptop_offload`).
  - **Mitigation:** Enforce the smoke-test matrix on every infra-impacting change.
- **Risk:** Environment mismatch (audio/GPU/network tooling) causes false negatives.
  - **Mitigation:** Strengthen doctor/prereq checks and fail before launch.

## Suggested Execution Order
1. A (Repo Hygiene)
2. D1 (Config wiring audit)
3. C (Launch architecture normalization)
4. B (Topic contract + validator)
5. E (Docker/runtime prerequisites)
6. D2 + F (Validation automation and sign-off)

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

