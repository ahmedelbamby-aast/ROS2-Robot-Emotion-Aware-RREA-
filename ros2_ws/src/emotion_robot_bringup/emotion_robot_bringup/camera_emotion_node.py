import rclpy
from rclpy.node import Node
from sensor_msgs.msg import Image
from std_msgs.msg import String

from .vision_helpers import classify_camera_emotion


class CameraEmotionNode(Node):
    def __init__(self):
        super().__init__("camera_emotion_node")
        self.declare_parameter("input_topic", "/camera/image_raw")
        self.declare_parameter("output_topic", "/camera/emotion")
        self.declare_parameter("use_deepface", True)
        self.declare_parameter("face_cascade_path", "")
        self.declare_parameter("deepface_detector_backend", "opencv")
        self.declare_parameter("deepface_min_score", 35.0)
        self.declare_parameter("deepface_min_margin", 8.0)

        input_topic = str(self.get_parameter("input_topic").value or "/camera/image_raw")
        output_topic = str(self.get_parameter("output_topic").value or "/camera/emotion")
        self._use_deepface = bool(self.get_parameter("use_deepface").value)
        self._face_cascade_path = str(self.get_parameter("face_cascade_path").value or "").strip()
        self._deepface_detector_backend = str(self.get_parameter("deepface_detector_backend").value or "opencv").strip()
        self._deepface_min_score = float(self.get_parameter("deepface_min_score").value)
        self._deepface_min_margin = float(self.get_parameter("deepface_min_margin").value)

        self.pub = self.create_publisher(String, output_topic, 10)
        self.create_subscription(Image, input_topic, self.on_image, 10)

        self._cv2 = None
        self._deepface = None
        try:
            import cv2  # type: ignore

            self._cv2 = cv2
        except Exception as exc:
            self.get_logger().warning(f"OpenCV unavailable, camera emotion fallback to neutral: {exc}")

        if self._use_deepface:
            try:
                from deepface import DeepFace  # type: ignore

                self._deepface = DeepFace
            except Exception as exc:
                self.get_logger().warning(f"DeepFace unavailable, using OpenCV-only fallback: {exc}")

    def on_image(self, msg: Image):
        result = classify_camera_emotion(
            msg,
            cv2_module=self._cv2,
            deepface_cls=self._deepface,
            use_deepface=self._use_deepface,
            cascade_path=(self._face_cascade_path or None),
            deepface_detector_backend=self._deepface_detector_backend,
            deepface_min_score=self._deepface_min_score,
            deepface_min_margin=self._deepface_min_margin,
        )
        out = String()
        out.data = result.emotion
        self.pub.publish(out)


def main():
    rclpy.init()
    node = CameraEmotionNode()
    rclpy.spin(node)
    node.destroy_node()
    rclpy.shutdown()
