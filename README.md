# Emotion Robot (RREA)

ROS 2 Humble + Docker deployment for emotion-aware interaction with two runtime modes:

- `robot_only`: all processing on Mustar robot host
- `laptop_offload`: robot publishes camera/audio feed, laptop runs inference, robot speaks response

Primary runbooks:

- [INSTALLATION.md](INSTALLATION.md)
- [QUICKSTART.md](QUICKSTART.md)

## Real-World Deployment Notes (May 20, 2026)

- Mustar deployments are SSH-first and typically headless.
- Ubuntu 18.04 hosts should use Docker CLI engine only (no Docker Desktop).
- This repo requires Docker Compose v2 plugin (`docker compose ...`), not legacy `docker-compose` v1.
- ORBBEC ASTRA is non-UVC in this project path; use USB bus pass-through + OpenNI path, not `/dev/video*` assumptions.

## Architecture (Dual Mode)

### 1) Robot-only

- Robot container captures camera/mic, runs full pipeline, sends `/robot/say` to local TTS.

### 2) Laptop offload

- Robot side: camera/audio acquisition + gateway client.
- Laptop side: inference gateway server + modality/fusion/response nodes.
- Robot side output: receives response and publishes speaker output.

Operational order for offload mode:

1. Launch laptop inference first.
2. Launch robot endpoint second.
3. Confirm gateway connection in logs before validation.

## Mustar SSH Setup (Operator Baseline)

Run on operator laptop:

```bash
ssh-keygen -t ed25519 -C "mustar-ops" -f ~/.ssh/mustar_ed25519
ssh-copy-id -i ~/.ssh/mustar_ed25519.pub <mustar_user>@<mustar_ip>
ssh -i ~/.ssh/mustar_ed25519 <mustar_user>@<mustar_ip>
```

Optional `~/.ssh/config` profile:

```sshconfig
Host mustar
  HostName <mustar_ip>
  User <mustar_user>
  IdentityFile ~/.ssh/mustar_ed25519
  ServerAliveInterval 30
  ServerAliveCountMax 4
```

Then use:

```bash
ssh mustar
```

## One-Command Mustar Deploy

```bash
cd ROS2-Robot-Emotion-Aware-RREA-
scripts/deploy_mustar.sh robot_only
```

Offload variant:

```bash
scripts/deploy_mustar.sh laptop_offload
```

`deploy_mustar.sh` performs host/container AV checks, builds images, predownloads Whisper/HF models, builds `ros2_ws`, then launches the selected bringup.

## Camera Constraints (ORBBEC ASTRA)

- ASTRA is treated as `vision.source=astra` with `/dev/bus/usb` mapping.
- UVC mode (`vision.source=uvc`) expects `/dev/video0` or `/dev/video1`.
- Do not mix ASTRA and UVC assumptions in the same runbook.

Set ASTRA mode:

```bash
scripts/config.sh set vision.source astra
scripts/up.sh
```

## Model Predownload Workflow

Model warm-up is required on first run (or after cache cleanup):

- Whisper `base`
- HF sentiment model `cardiffnlp/twitter-roberta-base-sentiment-latest`

Predownload is automatic in `scripts/deploy_mustar.sh`. Manual container predownload:

```bash
docker compose -f docker/docker-compose.yml exec -T robot bash -lc "python3 - <<'PY'
from huggingface_hub import snapshot_download
import whisper
whisper.load_model('base')
snapshot_download(repo_id='cardiffnlp/twitter-roberta-base-sentiment-latest')
print('prefetch complete')
PY"
```

## Known Blockers and Workarounds

- `docker-compose: command not found` or v1 syntax mismatch.
  - Workaround: install Compose v2 plugin and use `docker compose`.
- ASTRA not detected via `/dev/video*`.
  - Workaround: `vision.source=astra`, pass `/dev/bus/usb`, validate `lsusb` vendor `2bc5`.
- Offload mode starts but no inference results.
  - Workaround: ensure laptop inference is launched before robot endpoint; confirm host/port from config.
- First inference cycle is very slow.
  - Workaround: run predownload workflow before demo/runtime validation.

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

