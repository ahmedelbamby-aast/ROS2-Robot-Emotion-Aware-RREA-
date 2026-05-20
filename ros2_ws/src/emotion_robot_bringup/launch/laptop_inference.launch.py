from launch import LaunchDescription
from launch_ros.actions import Node
from emotion_robot_bringup.common import load_project_config


def generate_launch_description():
    cfg = load_project_config() or {}
    audio_cfg = cfg.get("audio", {})
    stt_cfg = cfg.get("stt", {})
    tts_cfg = cfg.get("tts", {})

    audio_emotion_topic = str(audio_cfg.get("emotion_topic", "/audio/emotion"))
    transcript_topic = str(stt_cfg.get("transcript_topic", "/speech/text"))
    tts_output_topic = str(tts_cfg.get("output_topic", "/robot/say"))

    return LaunchDescription([
        Node(
            package="emotion_robot_bringup",
            executable="laptop_gateway_node",
            output="screen",
            remappings=[
                ("/speech/text", transcript_topic),
                ("/robot/say", tts_output_topic),
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
    ])
