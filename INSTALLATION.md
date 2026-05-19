# Installation Guide

This guide covers full setup for Linux and Windows.

## 1. Repository Layout

Expected root:

- `emotion_robot/`
- `emotion_robot/docker/`
- `emotion_robot/scripts/`
- `emotion_robot/scripts/windows/`
- `emotion_robot/config/project.yaml`

## 2. Linux Installation (Ubuntu 22.04+ Recommended)

### 2.1 Prerequisites

Install required system tools:

```bash
sudo apt-get update
sudo apt-get install -y \
  ca-certificates curl gnupg lsb-release \
  python3 python3-pip git
```

Install Docker Engine + Docker Compose plugin (official Docker docs method):

```bash
sudo install -m 0755 -d /etc/apt/keyrings
curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo gpg --dearmor -o /etc/apt/keyrings/docker.gpg
sudo chmod a+r /etc/apt/keyrings/docker.gpg

echo \
  "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] https://download.docker.com/linux/ubuntu \
  $(. /etc/os-release && echo "$VERSION_CODENAME") stable" | \
  sudo tee /etc/apt/sources.list.d/docker.list > /dev/null

sudo apt-get update
sudo apt-get install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin
```

Add your user to docker group (to avoid `docker.sock` permission errors):

```bash
sudo usermod -aG docker "$USER"
newgrp docker
```

Verify:

```bash
docker --version
docker compose version
docker info
```

### 2.2 Project Dependencies

From project root:

```bash
cd emotion_robot
python3 -m pip install --user pyyaml
```

### 2.3 Optional: ngrok for `ngrok_tcp`

If using `gateway.transport=ngrok_tcp`, create ngrok account and export token:

```bash
export NGROK_AUTHTOKEN=<your_token>
```

### 2.4 Build Images

```bash
cd emotion_robot
scripts/build.sh
```

### 2.5 Start Containers

```bash
scripts/up.sh
```

Health check:

```bash
docker compose -f docker/docker-compose.yml ps
scripts/doctor.sh
```

## 3. Windows Installation (Windows 10/11 + Docker Desktop)

### 3.1 Prerequisites

Install:

- Docker Desktop (WSL2 backend enabled)
- Python 3.10+
- Git for Windows
- PowerShell 7+ (recommended)

Enable Docker Desktop integration for your WSL distro if you use WSL.

Verify in PowerShell:

```powershell
docker --version
docker compose version
python --version
```

### 3.2 Execution Policy

Allow local scripts for current user (once):

```powershell
Set-ExecutionPolicy -Scope CurrentUser RemoteSigned
```

### 3.3 Project Dependencies

```powershell
cd emotion_robot
.\scripts\windows\install_deps.ps1
```

### 3.4 Optional: ngrok for `ngrok_tcp`

```powershell
$env:NGROK_AUTHTOKEN = "<your_token>"
```

### 3.5 Build + Start

```powershell
.\scripts\windows\build.ps1
.\scripts\windows\up.ps1
```

Health check:

```powershell
.\scripts\windows\doctor.ps1
docker compose -f docker/docker-compose.yml ps
```

## 4. Runtime Modes

Set mode and transport with config scripts.

Linux:

```bash
scripts/config.sh set deployment.mode robot_only
scripts/config.sh set gateway.transport local_tcp
```

Windows:

```powershell
.\scripts\windows\config.ps1 set deployment.mode robot_only
.\scripts\windows\config.ps1 set gateway.transport local_tcp
```

Supported:

- `deployment.mode`: `robot_only` | `laptop_offload`
- `gateway.transport`: `local_tcp` | `ngrok_tcp`
- `inference.backend`: `auto` | `cpu` | `openvino` | `tensorrt`

## 5. Audio I/O and STT/TTS Configuration

Default config path: `config/project.yaml`

Relevant keys:

- `audio.input_topic`, `audio.emotion_topic`, `audio.sample_rate_hz`, `audio.chunk_bytes`
- `stt.enabled`, `stt.backend`, `stt.language`, `stt.transcript_topic`
- `tts.enabled`, `tts.backend`, `tts.voice`, `tts.output_topic`

Linux commands:

```bash
scripts/config.sh get audio.sample_rate_hz
scripts/config.sh set audio.sample_rate_hz 16000
scripts/config.sh set stt.enabled true
scripts/config.sh set stt.language en-US
scripts/config.sh set tts.enabled true
scripts/config.sh set tts.voice default
```

Windows PowerShell commands:

```powershell
.\scripts\windows\config.ps1 get audio.sample_rate_hz
.\scripts\windows\config.ps1 set audio.sample_rate_hz 16000
.\scripts\windows\config.ps1 set stt.enabled true
.\scripts\windows\config.ps1 set stt.language en-US
.\scripts\windows\config.ps1 set tts.enabled true
.\scripts\windows\config.ps1 set tts.voice default
```

`robot_only` run sequence:

Linux:

```bash
scripts/config.sh set deployment.mode robot_only
scripts/up.sh
docker compose -f docker/docker-compose.yml exec robot bash -lc "source /opt/ros/humble/setup.bash && source /workspace/ros2_ws/install/setup.bash && ros2 launch emotion_robot_bringup robot_only.launch.py"
```

Windows:

```powershell
.\scripts\windows\config.ps1 set deployment.mode robot_only
.\scripts\windows\up.ps1
.\scripts\windows\launch_robot_only.ps1
```

`laptop_offload` run sequence:

Linux:

```bash
scripts/config.sh set deployment.mode laptop_offload
scripts/config.sh set gateway.transport local_tcp
scripts/up.sh
docker compose -f docker/docker-compose.yml exec laptop bash -lc "source /opt/ros/humble/setup.bash && source /workspace/ros2_ws/install/setup.bash && ros2 launch emotion_robot_bringup laptop_inference.launch.py"
export ROBOT_GATEWAY_HOST=127.0.0.1
docker compose -f docker/docker-compose.yml exec robot bash -lc "source /opt/ros/humble/setup.bash && source /workspace/ros2_ws/install/setup.bash && ros2 launch emotion_robot_bringup robot_endpoint.launch.py"
```

Windows:

```powershell
.\scripts\windows\config.ps1 set deployment.mode laptop_offload
.\scripts\windows\config.ps1 set gateway.transport local_tcp
.\scripts\windows\up.ps1
.\scripts\windows\launch_laptop_inference.ps1
$env:ROBOT_GATEWAY_HOST = "127.0.0.1"
.\scripts\windows\launch_robot_endpoint.ps1
```

## 6. Common Troubleshooting

### 6.1 Docker socket permission denied (Linux)

Symptom:

- `permission denied while trying to connect to the docker API`

Fix:

```bash
sudo usermod -aG docker "$USER"
newgrp docker
```

### 6.2 `emotion_robot_base:latest` not found

Build base image first:

```bash
scripts/build.sh
```

### 6.3 `robot_endpoint` connection refused

Cause: laptop gateway is not running.

Fix:

1. Start containers with `scripts/up.sh`
2. Start laptop launch first (`laptop_inference.launch.py`)
3. Then start robot endpoint launch

### 6.4 ngrok not reachable

Check:

- token env var is set
- ngrok container running
- `runtime/ngrok.env` generated

Linux:

```bash
scripts/ngrok-url.sh
```

Windows:

```powershell
.\scripts\windows\ngrok-url.ps1
```

## 7. Cleanup

Linux:

```bash
scripts/down.sh
scripts/clean.sh
```

Windows:

```powershell
.\scripts\windows\down.ps1
.\scripts\windows\clean.ps1
```
