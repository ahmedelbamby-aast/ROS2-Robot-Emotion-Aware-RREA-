# QUICKSTART

This is the fastest reliable path to run the project in Linux or Windows.

## Current State Before You Run

- `DONE`: core pipeline topics are present and wired through launch flows.
- `PARTIAL`: model quality is not final yet.
  - vision and audio emotion currently include heuristic fallback behavior.
  - STT backend selection is wired but not final Whisper-first production behavior.
- Use [tasks.md](/home/mohamed/Desktop/Cognitive%20Project/ROS2-Robot-Emotion-Aware-RREA-/tasks.md) as source of truth for remaining work.

## A. Linux Quickstart

### A0. One-Command Mustar Deploy (Recommended)

For Mustar on-board camera/mic/speaker:

```bash
cd ROS2-Robot-Emotion-Aware-RREA-
scripts/deploy_mustar.sh robot_only
```

This single command verifies audio/video devices, builds `ros2_ws`, and launches the correct bringup.

For laptop offload:

```bash
scripts/deploy_mustar.sh laptop_offload
```

### A1. Build and Start Containers

```bash
cd ROS2-Robot-Emotion-Aware-RREA-
scripts/build.sh
scripts/up.sh
docker compose -f docker/docker-compose.yml ps
```

Expected:

- `emotion_robot-robot-1` is `Up`
- `emotion_robot-laptop-1` is `Up` (in `laptop_offload` mode)

### A2. Robot-Only Mode

Set mode and start:

```bash
scripts/config.sh set deployment.mode robot_only
scripts/up.sh
```

Launch robot-only pipeline:

```bash
docker compose -f docker/docker-compose.yml exec robot bash -lc "source /opt/ros/humble/setup.bash && source /workspace/ros2_ws/install/setup.bash && ros2 launch emotion_robot_bringup robot_only.launch.py"
```

### A3. Laptop-Offload Mode (Local TCP)

Set mode and transport:

```bash
scripts/config.sh set deployment.mode laptop_offload
scripts/config.sh set gateway.transport local_tcp
scripts/up.sh
```

Start laptop side first:

```bash
docker compose -f docker/docker-compose.yml exec laptop bash -lc "source /opt/ros/humble/setup.bash && source /workspace/ros2_ws/install/setup.bash && ros2 launch emotion_robot_bringup laptop_inference.launch.py"
```

In another terminal, start robot endpoint:

```bash
export ROBOT_GATEWAY_HOST=127.0.0.1
docker compose -f docker/docker-compose.yml exec robot bash -lc "source /opt/ros/humble/setup.bash && source /workspace/ros2_ws/install/setup.bash && ros2 launch emotion_robot_bringup robot_endpoint.launch.py"
```

Success signal:

- robot logs show `connected to laptop gateway at 127.0.0.1:8765`

### A4. Laptop-Offload Mode (ngrok TCP)

```bash
scripts/config.sh set deployment.mode laptop_offload
scripts/config.sh set gateway.transport ngrok_tcp
export NGROK_AUTHTOKEN=<your_token>
scripts/up.sh
scripts/ngrok-url.sh
```

Then run laptop launch locally and robot endpoint on robot host using generated `runtime/ngrok.env` values.

### A5. Stop / Clean

```bash
scripts/down.sh
scripts/clean.sh
```

### A6. Container Audio Test

After `scripts/up.sh`, verify and test container audio:

```bash
scripts/doctor.sh
scripts/audio-test.sh robot 3
```

For laptop container:

```bash
scripts/audio-test.sh laptop 3
```

## B. Windows Quickstart

### B1. Build and Start

```powershell
cd ROS2-Robot-Emotion-Aware-RREA-
.\scripts\windows\build.ps1
.\scripts\windows\up.ps1
docker compose -f docker/docker-compose.yml ps
```

### B2. Robot-Only Mode

```powershell
.\scripts\windows\config.ps1 set deployment.mode robot_only
.\scripts\windows\up.ps1
.\scripts\windows\launch_robot_only.ps1
```

### B3. Laptop-Offload (Local TCP)

```powershell
.\scripts\windows\config.ps1 set deployment.mode laptop_offload
.\scripts\windows\config.ps1 set gateway.transport local_tcp
.\scripts\windows\up.ps1
```

Start laptop side:

```powershell
.\scripts\windows\launch_laptop_inference.ps1
```

In another terminal:

```powershell
$env:ROBOT_GATEWAY_HOST = "127.0.0.1"
.\scripts\windows\launch_robot_endpoint.ps1
```

### B4. Laptop-Offload (ngrok TCP)

```powershell
.\scripts\windows\config.ps1 set gateway.transport ngrok_tcp
$env:NGROK_AUTHTOKEN = "<your_token>"
.\scripts\windows\up.ps1
.\scripts\windows\ngrok-url.ps1
```

### B5. Stop / Clean

```powershell
.\scripts\windows\down.ps1
.\scripts\windows\clean.ps1
```

### B6. Container Audio Test

After `.\scripts\windows\up.ps1`, verify and test container audio:

```powershell
.\scripts\windows\doctor.ps1
.\scripts\windows\audio-test.ps1 robot 3
```

For laptop container:

```powershell
.\scripts\windows\audio-test.ps1 laptop 3
```

## C. Verification Checklist

Run after startup:

- Linux: `scripts/doctor.sh`
- Windows: `.\scripts\windows\doctor.ps1`
- Container status: `docker compose -f docker/docker-compose.yml ps`
- Tests:

```bash
python3 -m pytest -q tests
python3 -m pytest -q ros2_ws/src/emotion_robot_bringup/test
```

Audio/STT/TTS mode + script behavior coverage:

```bash
python3 -m pytest -q tests/test_project_config.py tests/test_lib_config.py tests/test_up_script_modes.py
```

Windows PowerShell equivalent:

```powershell
python -m pytest -q tests/test_project_config.py tests/test_lib_config.py tests/test_up_script_modes.py
```

## D. Audio I/O + STT/TTS Usage

These commands configure audio capture/processing and STT/TTS toggles for both modes.

Important:

- STT/TTS config keys are launch-wired for `enabled`, `backend`, and output topics.
- Runtime fallback behavior is backend-dependent: `mock` maps to `none` for STT/TTS fallback mode.

Linux `robot_only`:

```bash
scripts/config.sh set deployment.mode robot_only
scripts/config.sh set audio.input_topic /audio/raw
scripts/config.sh set audio.emotion_topic /audio/emotion
scripts/config.sh set audio.sample_rate_hz 16000
scripts/config.sh set audio.chunk_bytes 4096
scripts/config.sh set stt.enabled true
scripts/config.sh set stt.backend whisper
scripts/config.sh set tts.enabled true
scripts/config.sh set tts.backend pyttsx3
scripts/up.sh
```

Fallback run:

```bash
scripts/config.sh set stt.backend mock
scripts/config.sh set tts.backend mock
scripts/up.sh
```

Windows `robot_only`:

```powershell
.\scripts\windows\config.ps1 set deployment.mode robot_only
.\scripts\windows\config.ps1 set audio.input_topic /audio/raw
.\scripts\windows\config.ps1 set audio.emotion_topic /audio/emotion
.\scripts\windows\config.ps1 set audio.sample_rate_hz 16000
.\scripts\windows\config.ps1 set audio.chunk_bytes 4096
.\scripts\windows\config.ps1 set stt.enabled true
.\scripts\windows\config.ps1 set stt.backend whisper
.\scripts\windows\config.ps1 set tts.enabled true
.\scripts\windows\config.ps1 set tts.backend pyttsx3
.\scripts\windows\up.ps1
```

Fallback run:

```powershell
.\scripts\windows\config.ps1 set stt.backend mock
.\scripts\windows\config.ps1 set tts.backend mock
.\scripts\windows\up.ps1
```

Linux `laptop_offload` (local TCP):

```bash
scripts/config.sh set deployment.mode laptop_offload
scripts/config.sh set gateway.transport local_tcp
scripts/config.sh set stt.enabled true
scripts/config.sh set tts.enabled true
scripts/up.sh
export ROBOT_GATEWAY_HOST=127.0.0.1
```

Windows `laptop_offload` (local TCP):

```powershell
.\scripts\windows\config.ps1 set deployment.mode laptop_offload
.\scripts\windows\config.ps1 set gateway.transport local_tcp
.\scripts\windows\config.ps1 set stt.enabled true
.\scripts\windows\config.ps1 set tts.enabled true
.\scripts\windows\up.ps1
$env:ROBOT_GATEWAY_HOST = \"127.0.0.1\"
```

## E. Notes from Actual Linux Execution

Validated in Linux environment on May 19, 2026:

- `scripts/build.sh` succeeded.
- `scripts/up.sh` succeeded and both services started.
- `scripts/doctor.sh` confirmed `/dev/snd` mapped for `robot`.
- `scripts/audio-test.sh robot 3` succeeded (capture + playback).
- `robot_only.launch.py` and `laptop_inference.launch.py` started successfully.
- `robot_endpoint.launch.py` connected successfully when laptop gateway was running concurrently.

## F. Phase Execution Checklist (Owner Ready)

- [ ] `PLAT` Build and bring up containers from clean checkout.
- [ ] `ROS` Launch `robot_only` and verify required topic graph.
- [ ] `ROS` Launch `laptop_offload` pair and verify gateway link and required topic graph.
- [ ] `QA` Run tests listed in section C and archive logs under `artifacts/phase3/`.
- [ ] `QA` Run `scripts/audio-test.sh robot 3` and `scripts/audio-test.sh laptop 3` where applicable.
- [ ] `DOCS` Update tracker status in [tasks.md](/home/mohamed/Desktop/Cognitive%20Project/ROS2-Robot-Emotion-Aware-RREA-/tasks.md) after each gate.
