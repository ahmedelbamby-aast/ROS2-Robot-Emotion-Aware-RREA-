from setuptools import setup

package_name = "emotion_robot_bringup"

setup(
    name=package_name,
    version="0.1.0",
    packages=[package_name],
    data_files=[
        ("share/ament_index/resource_index/packages", ["resource/" + package_name]),
        ("share/" + package_name, ["package.xml"]),
        ("share/" + package_name + "/launch", ["launch/robot_only.launch.py", "launch/robot_endpoint.launch.py", "launch/laptop_inference.launch.py"]),
    ],
    install_requires=["setuptools", "PyYAML", "speechrecognition", "pyttsx3"],
    zip_safe=True,
    maintainer="Eng.Ahmed Hany ElBamby",
    maintainer_email="ahmedelbamby1102003@gmail.com",
    description="Emotion robot bringup package.",
    license="MIT",
    entry_points={
        "console_scripts": [
            "robot_pipeline_node = emotion_robot_bringup.robot_pipeline_node:main",
            "robot_gateway_node = emotion_robot_bringup.robot_gateway_node:main",
            "laptop_gateway_node = emotion_robot_bringup.laptop_gateway_node:main",
            "laptop_inference_node = emotion_robot_bringup.laptop_inference_node:main",
            "stt_node = emotion_robot_bringup.stt_node:main",
            "tts_node = emotion_robot_bringup.tts_node:main",
        ],
    },
)
