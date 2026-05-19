import sys
if sys.prefix == '/usr':
    sys.real_prefix = sys.prefix
    sys.prefix = sys.exec_prefix = '/home/mohamed/Desktop/Cognitive Project/emotion_robot/ros2_ws/install/emotion_robot_bringup'
