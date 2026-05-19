from launch import LaunchDescription
from launch_ros.actions import Node


def generate_launch_description():
    return LaunchDescription([
        Node(package="emotion_robot_bringup", executable="laptop_gateway_node", output="screen"),
        Node(package="emotion_robot_bringup", executable="laptop_inference_node", output="screen"),
    ])
