# QUICKSTART

Last updated: May 20, 2026.

## 1. Preflight

```bash
docker --version
docker compose version
scripts/doctor.sh
```

If `docker compose` fails, install Compose v2 plugin before continuing.

## 2. Fastest Mustar Path

Robot-only:

```bash
cd ROS2-Robot-Emotion-Aware-RREA-
scripts/deploy_mustar.sh robot_only
```

Laptop offload:

```bash
scripts/deploy_mustar.sh laptop_offload
```

## 3. Manual Robot-only Path

```bash
scripts/config.sh set deployment.mode robot_only
scripts/up.sh
docker compose -f docker/docker-compose.yml exec robot bash -lc "source /opt/ros/humble/setup.bash && source /workspace/ros2_ws/install/setup.bash && ros2 launch emotion_robot_bringup robot_only.launch.py"
```

## 4. Manual Laptop Offload Path

```bash
scripts/config.sh set deployment.mode laptop_offload
scripts/config.sh set gateway.transport local_tcp
scripts/up.sh
```

Start laptop inference first:

```bash
docker compose -f docker/docker-compose.yml exec laptop bash -lc "source /opt/ros/humble/setup.bash && source /workspace/ros2_ws/install/setup.bash && ros2 launch emotion_robot_bringup laptop_inference.launch.py"
```

Then start robot endpoint:

```bash
export ROBOT_GATEWAY_HOST=127.0.0.1
docker compose -f docker/docker-compose.yml exec robot bash -lc "source /opt/ros/humble/setup.bash && source /workspace/ros2_ws/install/setup.bash && ros2 launch emotion_robot_bringup robot_endpoint.launch.py"
```

## 5. ASTRA vs UVC Camera Switch

ASTRA (non-UVC):

```bash
scripts/config.sh set vision.source astra
scripts/down.sh
scripts/up.sh
```

UVC:

```bash
scripts/config.sh set vision.source uvc
scripts/down.sh
scripts/up.sh
```

## 6. Predownload Models Before Demo

```bash
docker compose -f docker/docker-compose.yml exec -T robot bash -lc "python3 - <<'PY'
from huggingface_hub import snapshot_download
import whisper
whisper.load_model('base')
snapshot_download(repo_id='cardiffnlp/twitter-roberta-base-sentiment-latest')
print('prefetch complete')
PY"
```

Run for laptop container too when using offload mode.

## 7. Troubleshooting Shortlist

- No camera frames in ASTRA mode:
  - Verify `lsusb | grep -i -E 'orbbec|2bc5'`
  - Verify `/dev/bus/usb` exists on host
  - Re-run `scripts/deploy_mustar.sh ...`
- Offload mode no response:
  - Confirm laptop launch is running before robot endpoint
  - Confirm gateway host/port values from `config/project.yaml`
- STT/TTS silent:
  - Confirm `/dev/snd` mapped and test with `scripts/audio-test.sh robot 3`
