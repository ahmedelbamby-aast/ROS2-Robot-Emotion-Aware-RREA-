import sys
import types
import unittest
from pathlib import Path

PKG_ROOT = Path(__file__).resolve().parents[1]
if str(PKG_ROOT) not in sys.path:
    sys.path.insert(0, str(PKG_ROOT))


# Stub ROS imports so helper-only tests can import gateway modules without ROS runtime.
rclpy_mod = types.ModuleType("rclpy")
rclpy_mod.ok = lambda: True
sys.modules.setdefault("rclpy", rclpy_mod)

rclpy_node_mod = types.ModuleType("rclpy.node")
rclpy_node_mod.Node = object
sys.modules.setdefault("rclpy.node", rclpy_node_mod)


def _stub_msg_module(name, class_names):
    mod = types.ModuleType(name)
    for cls_name in class_names:
        setattr(mod, cls_name, type(cls_name, (), {}))
    sys.modules.setdefault(name, mod)


_stub_msg_module("std_msgs.msg", ["String", "UInt8MultiArray"])
_stub_msg_module("sensor_msgs.msg", ["Image"])
_stub_msg_module("nav_msgs.msg", ["Odometry"])
_stub_msg_module("tf2_msgs.msg", ["TFMessage"])
_stub_msg_module("diagnostic_msgs.msg", ["DiagnosticArray"])

from emotion_robot_bringup.laptop_gateway_node import route_incoming_topic  # noqa: E402
from emotion_robot_bringup.robot_gateway_node import (  # noqa: E402
    route_robot_incoming_topic,
    shape_audio_payload,
    shape_camera_payload,
    shape_odom_payload,
    shape_status_payload,
    shape_tf_payload,
)


class _Position:
    def __init__(self, x, y):
        self.x = x
        self.y = y


class _Pose:
    def __init__(self, x, y):
        self.position = _Position(x, y)


class _PoseWithCovariance:
    def __init__(self, x, y):
        self.pose = _Pose(x, y)


class _OdomMsg:
    def __init__(self, x, y):
        self.pose = _PoseWithCovariance(x, y)


class _ImageMsg:
    def __init__(self, width, height, encoding):
        self.width = width
        self.height = height
        self.encoding = encoding


class _AudioMsg:
    def __init__(self, data):
        self.data = data


class _TfMsg:
    def __init__(self, transforms):
        self.transforms = transforms


class _DiagStatus:
    def __init__(self, name, level):
        self.name = name
        self.level = level


class _DiagMsg:
    def __init__(self, statuses):
        self.status = statuses


class TestGatewayHelpers(unittest.TestCase):
    def test_laptop_route_mapping(self):
        self.assertEqual(route_incoming_topic("/camera/image_raw"), "/camera/emotion")
        self.assertEqual(route_incoming_topic("/audio/raw"), "/audio/emotion")
        self.assertEqual(route_incoming_topic("/odom"), "/speech/text")
        self.assertEqual(route_incoming_topic("/tf"), "/speech/text")
        self.assertEqual(route_incoming_topic("/robot/status"), "/speech/text")
        self.assertEqual(route_incoming_topic("/speech/text"), "/speech/text")
        self.assertIsNone(route_incoming_topic("/unknown"))

    def test_robot_reader_route_mapping(self):
        self.assertEqual(route_robot_incoming_topic("/emotion/final"), "emotion")
        self.assertEqual(route_robot_incoming_topic("/robot/response"), "response")
        self.assertEqual(route_robot_incoming_topic("/robot/say"), "say")
        self.assertIsNone(route_robot_incoming_topic("/unknown"))

    def test_camera_payload_fields(self):
        payload = shape_camera_payload(_ImageMsg(640, 480, "rgb8"), 123)
        self.assertEqual(
            payload,
            {
                "kind": "camera",
                "width": 640,
                "height": 480,
                "encoding": "rgb8",
                "stamp_ns": 123,
                "label": "neutral",
            },
        )

    def test_audio_payload_fields(self):
        payload = shape_audio_payload(_AudioMsg([1, 2, 3, 4]), 99)
        self.assertEqual(payload, {"kind": "audio", "bytes": 4, "stamp_ns": 99, "label": "calm"})

    def test_odom_payload_fields(self):
        payload = shape_odom_payload(_OdomMsg(1.23456, -2.34567), 77)
        self.assertEqual(payload, {"kind": "odom", "x": 1.235, "y": -2.346, "stamp_ns": 77})

    def test_tf_payload_fields(self):
        payload = shape_tf_payload(_TfMsg([object(), object(), object()]), 42)
        self.assertEqual(payload, {"kind": "tf", "frames": 3, "stamp_ns": 42})

    def test_status_payload_fields(self):
        payload = shape_status_payload(_DiagMsg([_DiagStatus("motor_ok", 1)]), 555)
        self.assertEqual(payload, {"kind": "status", "status": "motor_ok", "level": 1, "stamp_ns": 555})

    def test_status_payload_defaults_when_empty(self):
        payload = shape_status_payload(_DiagMsg([]), 556)
        self.assertEqual(payload, {"kind": "status", "status": "ok", "level": 0, "stamp_ns": 556})


if __name__ == "__main__":
    unittest.main()
