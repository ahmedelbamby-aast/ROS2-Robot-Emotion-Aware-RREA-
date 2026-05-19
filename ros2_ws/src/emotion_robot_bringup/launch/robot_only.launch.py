from launch import LaunchDescription
from launch_ros.actions import Node


def generate_launch_description():
    return LaunchDescription([
        Node(package="emotion_robot_bringup", executable="stt_node", output="screen"),
        Node(package="emotion_robot_bringup", executable="robot_pipeline_node", output="screen"),
        Node(package="emotion_robot_bringup", executable="tts_node", output="screen"),
    ])
