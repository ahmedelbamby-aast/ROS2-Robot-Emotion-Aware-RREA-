from __future__ import annotations

import sys
from pathlib import Path


# Make ROS2 package sources importable during unscoped pytest collection.
BRINGUP_SRC = Path(__file__).resolve().parent / "ros2_ws" / "src" / "emotion_robot_bringup"
if str(BRINGUP_SRC) not in sys.path:
    sys.path.insert(0, str(BRINGUP_SRC))
