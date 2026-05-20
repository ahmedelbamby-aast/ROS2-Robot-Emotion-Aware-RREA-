# Phase 2 Tasks - Modalities Pipeline

## Scope
Phase 2 covers these modality and behavior streams:
- Vision emotion (`/camera/image_raw` -> `/camera/emotion`)
- Audio emotion (`/audio/raw` -> `/audio/emotion`)
- STT (`/audio/raw` + `/audio/raw_text` -> `/speech/text`)
- NLP sentiment (`/speech/text` -> `/text/sentiment`)
- Fusion (`/camera/emotion` + `/audio/emotion` + `/text/sentiment` -> `/emotion/final`)
- Response policy (`/emotion/final` + `/speech/text` -> `/robot/response`, `/robot/say`)
- TTS (`/robot/say` -> speaker + `/speech/tts_status`)

## Checklist-Point Mapping
Use this as the execution tracker. Mark done only when all linked acceptance criteria pass.

| Checklist ID | Checkpoint | Related Task IDs |
|---|---|---|
| C2-01 | Vision emotion node is deterministic and robust on invalid frames | V-01, V-02, V-03 |
| C2-02 | Audio emotion classification handles silence/noise/short chunks | A-01, A-02, A-03 |
| C2-03 | STT publishes transcript or controlled fallback with cooldown | S-01, S-02, S-03, S-04 |
| C2-04 | NLP sentiment normalization is stable for positive/neutral/negative inputs | N-01, N-02 |
| C2-05 | Fusion emits only changed final emotion and respects precedence policy | F-01, F-02, F-03 |
| C2-06 | Response text and say outputs stay synchronized with final emotion context | R-01, R-02, R-03 |
| C2-07 | TTS backend reports readiness, degrades safely, and never blocks pipeline | T-01, T-02, T-03 |
| C2-08 | End-to-end modality pipeline passes robot_only smoke test | E-01, E-02 |
| C2-09 | End-to-end modality pipeline passes laptop_offload smoke test | E-03, E-04 |
| C2-10 | Regression tests cover all modality helper logic and key topic contracts | Q-01, Q-02, Q-03 |

## Dependencies Graph (High-Level)
- Vision, Audio emotion, and STT can be developed in parallel.
- NLP sentiment depends on STT output contract (`/speech/text`).
- Fusion depends on Vision + Audio emotion + NLP sentiment contracts.
- Response depends on Fusion output contract.
- TTS depends on Response `/robot/say` contract.
- End-to-end validation depends on all modality nodes and launch wiring.

## Task Backlog

### Vision Emotion Tasks

- [ ] **V-01 - Input and output contract hardening**  
  **Subtasks:**
  - Verify subscription to `sensor_msgs/Image` on `/camera/image_raw`.
  - Validate behavior for zero-size and malformed metadata frames.
  - Enforce normalized output labels only.
  **Acceptance criteria:**
  - Publishing invalid frame dimensions yields `neutral` without exceptions.
  - Output topic `/camera/emotion` always contains normalized label set.
  **Dependencies:** none.

- [ ] **V-02 - Deterministic baseline classifier behavior**  
  **Subtasks:**
  - Lock deterministic branch behavior for small/medium/large frame classes.
  - Add explicit unit tests for boundary resolutions (e.g., 320x240, 1280x720).
  **Acceptance criteria:**
  - Same frame metadata always yields same label in tests.
  - Test coverage includes all decision branches in `_classify`.
  **Dependencies:** V-01.

- [ ] **V-03 - Runtime observability for vision stream**  
  **Subtasks:**
  - Add lightweight counters/logs for received frames and published labels.
  - Add health notes to quick verification steps.
  **Acceptance criteria:**
  - Operator can confirm node is processing frames at runtime from logs/topic echo.
  **Dependencies:** V-01.

### Audio Emotion Tasks

- [ ] **A-01 - Raw audio handling and guardrails**  
  **Subtasks:**
  - Validate conversion from `UInt8MultiArray` to bytes in all edge cases.
  - Ensure empty payload short-circuit behavior remains `neutral`.
  **Acceptance criteria:**
  - No crash on empty payloads and very short chunks.
  - Empty payload never emits non-neutral label.
  **Dependencies:** none.

- [ ] **A-02 - RMS threshold calibration workflow**  
  **Subtasks:**
  - Introduce calibration notes and fixtures for low/medium/high energy samples.
  - Add tests for threshold boundaries around current RMS cutoffs.
  **Acceptance criteria:**
  - Threshold behavior is reproducible in tests for `sad/neutral/happy/angry` paths.
  **Dependencies:** A-01.

- [ ] **A-03 - Topic-level integration check**  
  **Subtasks:**
  - Validate `/audio/raw` feed in containerized runtime.
  - Confirm `/audio/emotion` publish frequency and stability under burst input.
  **Acceptance criteria:**
  - Under a 60-second burst stream, node remains alive and continues publishing labels.
  **Dependencies:** A-01, A-02.

### STT Tasks

- [ ] **S-01 - Fallback policy and cooldown behavior**  
  **Subtasks:**
  - Validate `fallback_enabled`, `min_audio_bytes`, and cooldown parameter behavior.
  - Ensure fallback emission rate limits are enforced.
  **Acceptance criteria:**
  - Fallback text is not published more frequently than configured cooldown.
  - Payloads below minimum bytes do not spam transcript topic.
  **Dependencies:** none.

- [ ] **S-02 - Structured raw_text payload extraction contract**  
  **Subtasks:**
  - Validate extraction logic for known audio-text payload formats.
  - Add tests for malformed payload strings.
  **Acceptance criteria:**
  - Well-formed payload publishes parsed text.
  - Malformed payload safely falls back to fallback policy.
  **Dependencies:** S-01.

- [ ] **S-03 - Backend readiness and status telemetry**  
  **Subtasks:**
  - Validate status publication on `/speech/stt_status` for each backend state.
  - Ensure startup and failure states are explicit.
  **Acceptance criteria:**
  - Status topic reports clear `ready=true/false` states.
  - Backend init failures do not terminate node.
  **Dependencies:** S-01.

- [ ] **S-04 - Microphone mode non-blocking operation**  
  **Subtasks:**
  - Verify polling timer cannot deadlock spin loop.
  - Confirm error paths revert to fallback behavior.
  **Acceptance criteria:**
  - Node remains responsive during microphone errors/timeouts.
  **Dependencies:** S-03.

### NLP Sentiment Tasks

- [ ] **N-01 - Sentiment classifier normalization contract**  
  **Subtasks:**
  - Validate sentiment outputs map to canonical set.
  - Add tests for mixed-case, empty, punctuation-heavy text.
  **Acceptance criteria:**
  - `/text/sentiment` only emits normalized labels.
  - Empty or ambiguous text maps to neutral.
  **Dependencies:** S-02.

- [ ] **N-02 - Domain phrase coverage for robot dialogues**  
  **Subtasks:**
  - Add phrase fixtures from likely robot-user interactions.
  - Expand sentiment terms without regressing existing tests.
  **Acceptance criteria:**
  - New phrase list improves expected polarity match rate in tests.
  **Dependencies:** N-01.

### Fusion Tasks

- [ ] **F-01 - Multi-modal state update correctness**  
  **Subtasks:**
  - Validate each modality callback updates only its own state.
  - Ensure default state is neutral for all three channels.
  **Acceptance criteria:**
  - Unit tests prove no cross-channel state corruption.
  **Dependencies:** V-02, A-02, N-01.

- [ ] **F-02 - Publish-on-change behavior**  
  **Subtasks:**
  - Validate duplicate final emotions are suppressed.
  - Add tests covering oscillation and repeated inputs.
  **Acceptance criteria:**
  - Repeated identical modal inputs do not republish `/emotion/final`.
  **Dependencies:** F-01.

- [ ] **F-03 - Policy weighting validation**  
  **Subtasks:**
  - Encode expected outcomes for conflicting modality cases.
  - Align tests with `emotion_policy.fuse_emotions` decision intent.
  **Acceptance criteria:**
  - Conflict matrix tests pass for at least 12 mixed combinations.
  **Dependencies:** F-01.

### Response Tasks

- [ ] **R-01 - Response payload consistency**  
  **Subtasks:**
  - Validate `/robot/response` and `/robot/say` are generated from same policy call.
  - Ensure missing speech context still yields coherent response.
  **Acceptance criteria:**
  - For each final emotion input, both outputs are published and semantically aligned.
  **Dependencies:** F-02.

- [ ] **R-02 - Latest-text context handling**  
  **Subtasks:**
  - Validate ordering behavior when emotion arrives before transcript update.
  - Define expected handling for stale/empty `latest_text`.
  **Acceptance criteria:**
  - Tests capture and approve behavior for stale text edge case.
  **Dependencies:** R-01, S-02.

- [ ] **R-03 - Response safety and tone constraints**  
  **Subtasks:**
  - Add checks to avoid extreme/unsafe phrasing for negative emotions.
  - Add policy fixtures for neutral fallback tone.
  **Acceptance criteria:**
  - Safety/tone fixtures pass and no unsafe text is emitted in tests.
  **Dependencies:** R-01.

### TTS Tasks

- [ ] **T-01 - Backend initialization and status contract**  
  **Subtasks:**
  - Validate status messages for enabled/disabled/unsupported/error states.
  - Verify pyttsx3 readiness path and fallback path are explicit.
  **Acceptance criteria:**
  - `/speech/tts_status` accurately indicates current TTS mode in all startup scenarios.
  **Dependencies:** R-01.

- [ ] **T-02 - Queue resilience under burst speech commands**  
  **Subtasks:**
  - Stress queue with rapid `/robot/say` messages.
  - Validate full-queue drop behavior and warning logging.
  **Acceptance criteria:**
  - Node does not crash under queue saturation and continues processing new messages after pressure drops.
  **Dependencies:** T-01.

- [ ] **T-03 - Non-blocking fallback log mode**  
  **Subtasks:**
  - Validate runtime TTS errors switch to log fallback.
  - Ensure fallback mode still drains queue.
  **Acceptance criteria:**
  - When TTS engine fails at runtime, node remains active and logs fallback speech lines.
  **Dependencies:** T-01.

### End-to-End + Quality Tasks

- [ ] **E-01 - Robot-only end-to-end scenario**  
  **Subtasks:**
  - Launch `robot_only` stack and verify all modality topics are active.
  - Run scenario: camera + audio + transcript -> final emotion -> response -> tts status.
  **Acceptance criteria:**
  - One scripted run produces all expected topic outputs without node crash.
  **Dependencies:** V-03, A-03, S-03, N-01, F-02, R-01, T-01.

- [ ] **E-02 - Robot-only soak test (15+ min)**  
  **Subtasks:**
  - Run sustained mixed modality inputs for 15 minutes.
  - Monitor for memory growth, dropped publications, and dead nodes.
  **Acceptance criteria:**
  - No node restarts/crashes and no unbounded error spam over 15+ minutes.
  **Dependencies:** E-01.

- [ ] **E-03 - Laptop-offload local TCP scenario**  
  **Subtasks:**
  - Validate laptop inference + robot endpoint startup order.
  - Verify modality outputs remain coherent over gateway bridge.
  **Acceptance criteria:**
  - `/emotion/final` and `/robot/say` are observed on robot side with active gateway connection.
  **Dependencies:** E-01.

- [ ] **E-04 - Laptop-offload ngrok TCP scenario**  
  **Subtasks:**
  - Validate ngrok endpoint injection workflow and reconnect behavior.
  - Execute one remote-style modality pass-through scenario.
  **Acceptance criteria:**
  - Gateway reconnect and modality output path work with ngrok transport.
  **Dependencies:** E-03.

- [ ] **Q-01 - Unit test coverage uplift for modality helpers**  
  **Subtasks:**
  - Add/extend tests for `speech_helpers.py`, `sentiment_logic.py`, and `emotion_policy.py`.
  - Ensure branch coverage for key decision points.
  **Acceptance criteria:**
  - All modality helper tests pass in CI/local and cover new branches.
  **Dependencies:** V-02, A-02, S-02, N-02, F-03, R-03.

- [ ] **Q-02 - Node contract smoke tests**  
  **Subtasks:**
  - Add lightweight tests for expected topic names and message types per node.
  - Validate node startup without optional external backends.
  **Acceptance criteria:**
  - Smoke tests pass without requiring microphone or physical speaker hardware.
  **Dependencies:** Q-01.

- [ ] **Q-03 - Documentation and verification checklist update**  
  **Subtasks:**
  - Sync `QUICKSTART.md` verification section with Phase 2 checks.
  - Add a concise command block for modality validation steps.
  **Acceptance criteria:**
  - Operator can run a single ordered checklist and verify all C2 checkpoints.
  **Dependencies:** C2-01 through C2-09 completion.

## Suggested Execution Order
1. Parallel track A: V-01..V-03 + A-01..A-03 + S-01..S-04.
2. Parallel track B: N-01..N-02 and F-01..F-03.
3. Sequential: R-01..R-03 -> T-01..T-03.
4. Integration: E-01..E-04.
5. Quality closeout: Q-01..Q-03.

## Definition of Done (Phase 2)
- All checklist points `C2-01` to `C2-10` are checked.
- All task IDs in this file are checked with linked evidence (test output or run logs).
- End-to-end runs pass in both deployment modes (`robot_only`, `laptop_offload`).
- No modality node crashes during soak testing window.
