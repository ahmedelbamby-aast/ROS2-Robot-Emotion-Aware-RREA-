# Config Wiring Audit

This file maps `config/project.yaml` keys to runtime consumers.

## Field Constraints (May 20, 2026)

- Compose invocation is v2 only (`docker compose`); legacy `docker-compose` v1 is unsupported in this repo scripts path.
- `vision.source=astra` must be treated as non-UVC camera mode with USB bus mapping.
- `deployment.mode=laptop_offload` requires startup ordering:
  1. laptop inference launch
  2. robot endpoint launch
- `scripts/deploy_mustar.sh` now includes model predownload (Whisper + HF sentiment model) and should be preferred for first-run reliability.

Legend:
- `Wired`: key affects runtime behavior now.
- `Partial`: key exists but behavior is incomplete or indirect.
- `Not Wired`: key currently unused in runtime path.

| Key | Consumer | Status | Notes |
| --- | --- | --- | --- |
| `deployment.mode` | `scripts/up.sh`, `scripts/windows/up.ps1` | Wired | Chooses `robot_only` vs `laptop_offload` service startup. |
| `gateway.transport` | `scripts/up.sh`, `scripts/windows/up.ps1` | Wired | Chooses `local_tcp` vs `ngrok_tcp` path. |
| `gateway.port` | gateway nodes, `up` scripts env | Wired | Used for listen/connect target. |
| `gateway.local_host` | robot endpoint startup instructions | Wired | Used in local TCP mode. |
| `ngrok.authtoken_env` | `up` scripts | Wired | Reads token env var name. |
| `ngrok.use_ephemeral_tcp` | `scripts/up.sh` | Wired | Controls ngrok URL fetch path. |
| `inference.backend` | `scripts/doctor.sh` | Partial | Checked in doctor, not deeply used by modality nodes yet. |
| `inference.device` | none | Not Wired | Placeholder for future compute selection. |
| `audio.input_topic` | launch remap (`robot_only`, `robot_endpoint`, `system`) | Wired | Remaps STT/audio-emotion input from `/audio/raw`. |
| `audio.emotion_topic` | launch remap (`robot_only`, `laptop_inference`, `system`) | Wired | Remaps fusion input/output path for `/audio/emotion`. |
| `audio.sample_rate_hz` | conceptual config | Partial | Not enforced in current nodes. |
| `audio.chunk_bytes` | conceptual config | Partial | Not enforced in current nodes. |
| `stt.enabled` | launch params -> `stt_node.enabled` | Wired | Applied in `robot_only`, `robot_endpoint`, `system`. |
| `stt.backend` | launch params -> `stt_node.backend`,`stt_node.model_backend` | Wired | `mock` normalized to `none` fallback mode. |
| `stt.language` | none | Not Wired | Reserved for backend integration. |
| `stt.transcript_topic` | launch param/remap | Wired | Passed to `stt_node.transcript_topic` and remapped consumers. |
| `tts.enabled` | launch params -> `tts_node.enabled` | Wired | Applied in `robot_only`, `robot_endpoint`, `system`. |
| `tts.backend` | launch params -> `tts_node.backend`,`tts_node.engine` | Wired | `mock` normalized to `none` fallback mode. |
| `tts.voice` | none | Not Wired | Reserved for richer TTS support. |
| `tts.output_topic` | launch param/remap | Wired | Passed to `tts_node.output_topic` and remapped producers. |

## Implementation Reality Notes

- New modality/fusion/response nodes exist and required checklist output topics are produced.
- Config wiring is complete for topic routing and STT/TTS backend toggles in launch/runtime integration.
- Current behavior is mixed:
  - some runtime behavior comes from config-driven scripts (`deployment`, `gateway`),
  - some comes from fixed topic names or launch-time node params.

## Immediate Wiring Priorities

1. Wire `stt.language` into backend-specific runtime behavior (Whisper and speech-recognition path).
2. Wire `tts.voice` into pyttsx3 voice selection.
3. Wire `audio.sample_rate_hz` and `audio.chunk_bytes` into capture/processing nodes.

## Phase 1 Completion Checklist

- [x] Mapping table created and committed.
- [ ] All remaining `Partial` and `Not Wired` rows either wired or explicitly deferred with owner/date.
- [ ] `scripts/doctor.sh` and runtime logs show effective values for critical runtime keys.
- [ ] Validation tests fail when critical keys are invalid or empty.
