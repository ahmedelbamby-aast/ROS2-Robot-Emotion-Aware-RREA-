import os

from launch.actions import ExecuteProcess, LogInfo


def build_camera_source_actions(vision_cfg: dict):
    source = str(vision_cfg.get("source", "uvc")).strip().lower()
    input_topic = str(vision_cfg.get("input_topic", "/camera/image_raw"))
    if source == "none":
        return [LogInfo(msg="[camera] source=none, skipping camera publisher startup")]

    env = {
        "CAMERA_SOURCE": source,
        "CAMERA_INPUT_TOPIC": input_topic,
        "CAMERA_UVC_DEVICE": str(vision_cfg.get("uvc_device", os.environ.get("VIDEO_DEVICE_PRIMARY", "/dev/video0"))),
        "CAMERA_ASTRA_BRIDGE_CMD": str(vision_cfg.get("astra_bridge_cmd", "")),
    }
    return [
        LogInfo(msg=f"[camera] source={source}, input_topic={input_topic}"),
        ExecuteProcess(
            cmd=["bash", "-lc", "/workspace/scripts/start_camera_source.sh"],
            output="screen",
            additional_env=env,
        ),
    ]
