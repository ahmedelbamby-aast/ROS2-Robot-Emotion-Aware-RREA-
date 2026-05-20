from launch import LaunchDescription
from launch_ros.actions import Node
from emotion_robot_bringup.common import load_project_config
from emotion_robot_bringup.camera_source_launch import build_camera_source_actions


def generate_launch_description():
    cfg = load_project_config() or {}
    audio_cfg = cfg.get("audio", {})
    vision_cfg = cfg.get("vision", {})
    stt_cfg = cfg.get("stt", {})
    tts_cfg = cfg.get("tts", {})

    audio_input_topic = str(audio_cfg.get("input_topic", "/audio/raw"))
    audio_emotion_topic = str(audio_cfg.get("emotion_topic", "/audio/emotion"))
    transcript_topic = str(stt_cfg.get("transcript_topic", "/speech/text"))
    tts_output_topic = str(tts_cfg.get("output_topic", "/robot/say"))

    stt_backend = str(stt_cfg.get("backend", "whisper")).strip().lower()
    if stt_backend == "mock":
        stt_backend = "none"

    tts_backend = str(tts_cfg.get("backend", "pyttsx3")).strip().lower()
    if tts_backend == "mock":
        tts_backend = "none"

    return LaunchDescription(build_camera_source_actions(vision_cfg) + [
        Node(
            package="emotion_robot_bringup",
            executable="camera_emotion_node",
            output="screen",
            parameters=[{
                "input_topic": str(vision_cfg.get("input_topic", "/camera/image_raw")),
                "output_topic": str(vision_cfg.get("emotion_topic", "/camera/emotion")),
                "use_deepface": bool(vision_cfg.get("use_deepface", True)),
                "face_cascade_path": str(vision_cfg.get("face_cascade_path", "")),
                "deepface_detector_backend": str(vision_cfg.get("deepface_detector_backend", "opencv")),
            }],
        ),
        Node(
            package="emotion_robot_bringup",
            executable="audio_emotion_node",
            output="screen",
            parameters=[{
                "sample_rate": int(audio_cfg.get("sample_rate", 16000)),
                "input_topic": audio_input_topic,
                "output_topic": audio_emotion_topic,
                "model_profile_path": str(audio_cfg.get("model_profile_path", "")),
            }],
            remappings=[
                ("/audio/raw", audio_input_topic),
                ("/audio/emotion", audio_emotion_topic),
            ],
        ),
        Node(
            package="emotion_robot_bringup",
            executable="stt_node",
            output="screen",
            parameters=[{
                "enabled": bool(stt_cfg.get("enabled", True)),
                "backend": stt_backend,
                "model_backend": stt_backend,
                "transcript_topic": transcript_topic,
                "audio_topic": audio_input_topic,
                "use_microphone": bool(stt_cfg.get("use_microphone", True)),
                "whisper_model_size": str(stt_cfg.get("whisper_model_size", stt_cfg.get("whisper_model", ""))),
                "whisper_language": str(stt_cfg.get("whisper_language", stt_cfg.get("language", ""))),
                "whisper_model_dir": str(stt_cfg.get("whisper_model_dir", "")),
                "whisper_device": str(stt_cfg.get("whisper_device", "")),
                "whisper_task": str(stt_cfg.get("whisper_task", "transcribe")),
                "whisper_fp16": bool(stt_cfg.get("whisper_fp16", False)),
                "whisper_temperature": float(stt_cfg.get("whisper_temperature", -1.0)),
            }],
            remappings=[
                ("/audio/raw", audio_input_topic),
                ("/speech/text", transcript_topic),
            ],
        ),
        Node(
            package="emotion_robot_bringup",
            executable="sentiment_node",
            output="screen",
            remappings=[
                ("/speech/text", transcript_topic),
            ],
        ),
        Node(
            package="emotion_robot_bringup",
            executable="fusion_node",
            output="screen",
            remappings=[
                ("/audio/emotion", audio_emotion_topic),
            ],
        ),
        Node(
            package="emotion_robot_bringup",
            executable="response_node",
            output="screen",
            remappings=[
                ("/speech/text", transcript_topic),
                ("/robot/say", tts_output_topic),
            ],
        ),
        Node(
            package="emotion_robot_bringup",
            executable="tts_node",
            output="screen",
            parameters=[{
                "backend": tts_backend,
                "engine": tts_backend,
                "enabled": bool(tts_cfg.get("enabled", True)),
                "output_topic": tts_output_topic,
            }],
            remappings=[
                ("/robot/say", tts_output_topic),
            ],
        ),
    ])
