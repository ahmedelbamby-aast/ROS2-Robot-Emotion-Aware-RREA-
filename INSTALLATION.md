# Installation Guide

Last updated: May 20, 2026.

This guide reflects current field setup patterns and known issues.

## 1. Linux Prerequisites

### 1.1 Ubuntu 18.04 (CLI-only Docker path)

Ubuntu 18.04 operators should use Docker Engine + CLI only.

```bash
sudo apt-get update
sudo apt-get install -y apt-transport-https ca-certificates curl gnupg-agent software-properties-common
curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo apt-key add -
sudo add-apt-repository \
  "deb [arch=$(dpkg --print-architecture)] https://download.docker.com/linux/ubuntu \
  $(lsb_release -cs) stable"
sudo apt-get update
sudo apt-get install -y docker-ce docker-ce-cli containerd.io
```

Install Docker Compose v2 plugin (required for this repo):

```bash
sudo mkdir -p /usr/local/lib/docker/cli-plugins
sudo curl -SL https://github.com/docker/compose/releases/download/v2.27.1/docker-compose-linux-$(uname -m) \
  -o /usr/local/lib/docker/cli-plugins/docker-compose
sudo chmod +x /usr/local/lib/docker/cli-plugins/docker-compose
```

Verify:

```bash
docker --version
docker compose version
```

### 1.2 Ubuntu 20.04/22.04+

Use Docker official apt repo and install plugin package:

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

## 2. Docker Group and Base Tools

```bash
sudo usermod -aG docker "$USER"
newgrp docker
sudo apt-get install -y python3 python3-pip git
```

## 3. Clone and Repo Dependency

```bash
git clone <repo_url>
cd ROS2-Robot-Emotion-Aware-RREA-
python3 -m pip install --user pyyaml
```

## 4. Mustar SSH Setup

```bash
ssh-keygen -t ed25519 -C "mustar-ops" -f ~/.ssh/mustar_ed25519
ssh-copy-id -i ~/.ssh/mustar_ed25519.pub <mustar_user>@<mustar_ip>
ssh -i ~/.ssh/mustar_ed25519 <mustar_user>@<mustar_ip>
```

Optional sync from laptop to robot:

```bash
rsync -avz --delete --exclude '.git' ./ <mustar_user>@<mustar_ip>:~/ROS2-Robot-Emotion-Aware-RREA-/
```

## 5. Configure Runtime Mode

```bash
scripts/config.sh set deployment.mode robot_only
scripts/config.sh set gateway.transport local_tcp
```

For ASTRA camera:

```bash
scripts/config.sh set vision.source astra
```

## 6. Build and Start

```bash
scripts/build.sh
scripts/up.sh
scripts/doctor.sh
```

## 7. One-Command Mustar Deployment

```bash
scripts/deploy_mustar.sh robot_only
```

or:

```bash
scripts/deploy_mustar.sh laptop_offload
```

## 8. Offload Sync Workflow (Robot + Laptop)

1. Start laptop side first:

```bash
docker compose -f docker/docker-compose.yml exec laptop bash -lc "source /opt/ros/humble/setup.bash && source /workspace/ros2_ws/install/setup.bash && ros2 launch emotion_robot_bringup laptop_inference.launch.py"
```

2. Start robot endpoint second:

```bash
export ROBOT_GATEWAY_HOST=127.0.0.1
docker compose -f docker/docker-compose.yml exec robot bash -lc "source /opt/ros/humble/setup.bash && source /workspace/ros2_ws/install/setup.bash && ros2 launch emotion_robot_bringup robot_endpoint.launch.py"
```

3. Validate connection in robot logs.

## 9. Predownload Models (Whisper + Hugging Face)

Automatic in `deploy_mustar.sh`. Manual predownload:

```bash
docker compose -f docker/docker-compose.yml exec -T robot bash -lc "python3 - <<'PY'
from huggingface_hub import snapshot_download
import whisper
whisper.load_model('base')
snapshot_download(repo_id='cardiffnlp/twitter-roberta-base-sentiment-latest')
print('prefetch complete')
PY"
```

## 10. Camera Troubleshooting Paths

UVC path:

```bash
scripts/config.sh set vision.source uvc
ls -l /dev/video0 /dev/video1
```

ASTRA path:

```bash
scripts/config.sh set vision.source astra
lsusb | grep -i -E 'orbbec|2bc5'
ls -l /dev/bus/usb
```

If ASTRA is present in `lsusb` but no frames:

1. Restart containers: `scripts/down.sh && scripts/up.sh`
2. Re-run `scripts/deploy_mustar.sh robot_only`
3. Confirm camera source startup command in logs (`openni2` bridge path)

## 11. Known Blockers and Workarounds

- Blocker: only `docker-compose` v1 installed.
  - Workaround: install Compose v2 plugin; use `docker compose`.
- Blocker: missing `/dev/snd` on host.
  - Workaround: host audio stack/permissions must be fixed before STT/TTS validation.
- Blocker: ngrok transport with missing token.
  - Workaround: export env var defined by `ngrok.authtoken_env` before `scripts/up.sh`.
- Blocker: first inference run stalls on model download.
  - Workaround: predownload models before integration tests/demos.
