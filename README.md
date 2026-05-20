# Emotion Robot

Docker-first ROS 2 Humble project with two deployment modes from `config/project.yaml`:

- `robot_only`
- `laptop_offload` with `gateway.transport` as `local_tcp` or `ngrok_tcp`

Detailed docs:

- [Installation Guide](INSTALLATION.md)
- [Quickstart Runbook](QUICKSTART.md)

## Audio/STT/TTS Configuration

The project config includes explicit audio I/O and STT/TTS knobs in `config/project.yaml`:

- `audio.input_topic` (default: `/audio/raw`)
- `audio.emotion_topic` (default: `/audio/emotion`)
- `audio.sample_rate_hz` (default: `16000`)
- `audio.chunk_bytes` (default: `4096`)
- `stt.enabled` / `stt.backend` / `stt.language` / `stt.transcript_topic`
- `tts.enabled` / `tts.backend` / `tts.voice` / `tts.output_topic`

Current runtime note:

- `stt.enabled` and `tts.enabled` are now set to `true` in `config/project.yaml`.
- Launch files now map `stt.enabled`, `stt.backend`, `stt.transcript_topic`, `audio.input_topic`, `tts.enabled`, `tts.backend`, and `tts.output_topic` into node parameters/remaps.
- Fallback behavior: `stt.backend=mock` maps to `none` (fallback transcript path), and `tts.backend=mock` maps to `none` (log-only fallback instead of speaker output).

## Implementation Status Snapshot

- Implemented topics: `/camera/emotion`, `/audio/emotion`, `/speech/text`, `/text/sentiment`, `/emotion/final`, `/robot/response`, `/robot/say`.
- Implemented launch paths: `system.launch.py`, `robot_only.launch.py`, `laptop_inference.launch.py`, `robot_endpoint.launch.py`.
- Current partial area: emotion inference quality.
  - Vision and audio emotion nodes are wired with OpenCV/DeepFace/librosa dependencies, but runtime quality remains under validation.
  - STT backend path is wired for backend selection, but Whisper-first production behavior is still pending.
- Tracking docs:
  - [tasks.md](/home/mohamed/Desktop/Cognitive%20Project/ROS2-Robot-Emotion-Aware-RREA-/tasks.md)
  - [CONFIG_WIRING_AUDIT.md](/home/mohamed/Desktop/Cognitive%20Project/ROS2-Robot-Emotion-Aware-RREA-/CONFIG_WIRING_AUDIT.md)
  - [FOUNDATION_TOPIC_CONTRACT.md](/home/mohamed/Desktop/Cognitive%20Project/ROS2-Robot-Emotion-Aware-RREA-/FOUNDATION_TOPIC_CONTRACT.md)

Linux examples:

```bash
scripts/config.sh set deployment.mode robot_only
scripts/config.sh set audio.sample_rate_hz 16000
scripts/config.sh set stt.enabled true
scripts/config.sh set tts.enabled true
scripts/config.sh get stt.enabled
```

Windows PowerShell examples:

```powershell
.\scripts\windows\config.ps1 set deployment.mode robot_only
.\scripts\windows\config.ps1 set audio.sample_rate_hz 16000
.\scripts\windows\config.ps1 set stt.enabled true
.\scripts\windows\config.ps1 set tts.enabled true
.\scripts\windows\config.ps1 get stt.enabled
```

## Quick start

Fast one-command Mustar deployment (on-board camera/mic/speaker, Linux):

```bash
cd ROS2-Robot-Emotion-Aware-RREA-
scripts/deploy_mustar.sh robot_only
```

What it does:

- verifies host + container camera/mic/speaker devices
- builds images and `ros2_ws`
- launches the correct bringup (`robot_only` or `laptop_offload`)

Laptop-offload one-command variant:

```bash
scripts/deploy_mustar.sh laptop_offload
```

```bash
cd ROS2-Robot-Emotion-Aware-RREA-
scripts/build.sh
scripts/up.sh
```

Windows PowerShell quick start:

```powershell
cd ROS2-Robot-Emotion-Aware-RREA-
.\scripts\windows\build.ps1
.\scripts\windows\up.ps1
```

Robot-only launch:

```bash
docker compose -f docker/docker-compose.yml exec robot bash -lc "source /opt/ros/humble/setup.bash && source /workspace/ros2_ws/install/setup.bash && ros2 launch emotion_robot_bringup robot_only.launch.py"
```

Robot-only launch (Windows PowerShell):

```powershell
.\scripts\windows\launch_robot_only.ps1
```

Laptop-offload launch:

```bash
docker compose -f docker/docker-compose.yml exec laptop bash -lc "source /opt/ros/humble/setup.bash && source /workspace/ros2_ws/install/setup.bash && ros2 launch emotion_robot_bringup laptop_inference.launch.py"
docker compose -f docker/docker-compose.yml exec robot bash -lc "source /opt/ros/humble/setup.bash && source /workspace/ros2_ws/install/setup.bash && ros2 launch emotion_robot_bringup robot_endpoint.launch.py"
```

Laptop-offload launch (Windows PowerShell):

```powershell
.\scripts\windows\launch_laptop_inference.ps1
.\scripts\windows\launch_robot_endpoint.ps1
```

### Laptop-offload configuration details

`scripts/up.sh` behaves differently by `gateway.transport`:

- `local_tcp`: it prints the local target and you must export `ROBOT_GATEWAY_HOST` before launching the robot endpoint.
- `ngrok_tcp`: set the configured ngrok token env var (default from `config/project.yaml`: `NGROK_AUTHTOKEN`) before `scripts/up.sh`.

Examples:

```bash
# local_tcp
export ROBOT_GATEWAY_HOST=127.0.0.1
scripts/up.sh

# ngrok_tcp
export NGROK_AUTHTOKEN=<your_token>
scripts/up.sh
scripts/ngrok-url.sh
```

Windows script equivalents:

```powershell
.\scripts\windows\config.ps1 get deployment.mode
.\scripts\windows\build.ps1
.\scripts\windows\up.ps1
.\scripts\windows\doctor.ps1
.\scripts\windows\launch_robot_only.ps1
.\scripts\windows\launch_laptop_inference.ps1
.\scripts\windows\launch_robot_endpoint.ps1
.\scripts\windows\shell.ps1 robot
.\scripts\windows\down.ps1
.\scripts\windows\clean.ps1
.\scripts\windows\rebuild.ps1
.\scripts\windows\install_deps.ps1
```

### Container audio I/O (robot_only and laptop_offload)

- `scripts/up.sh` and `.\scripts\windows\up.ps1` now auto-map `/dev/snd` when available.
- Verify audio mapping with:
  - Linux: `scripts/doctor.sh`
  - Windows: `.\scripts\windows\doctor.ps1`
- Test mic capture and playback inside a running container:
  - Linux: `scripts/audio-test.sh robot 3` (or `laptop`)
  - Windows: `.\scripts\windows\audio-test.ps1 robot 3` (or `laptop`)
- Verified on Linux on May 19, 2026: `scripts/audio-test.sh robot 3` completed successfully.

## Test Coverage For Audio/STT/TTS + Mode Switching

Run integration/config tests from repo root:

```bash
python3 -m pytest -q tests/test_project_config.py tests/test_lib_config.py tests/test_up_script_modes.py
```

Windows PowerShell:

```powershell
python -m pytest -q tests/test_project_config.py tests/test_lib_config.py tests/test_up_script_modes.py
```
