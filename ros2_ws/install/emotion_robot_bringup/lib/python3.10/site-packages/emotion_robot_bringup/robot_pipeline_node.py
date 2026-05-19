from rclpy.node import Node
import rclpy
from std_msgs.msg import String


class RobotPipelineNode(Node):
    def __init__(self):
        super().__init__("robot_pipeline_node")
        self.pub_emotion = self.create_publisher(String, "/emotion/final", 10)
        self.pub_response = self.create_publisher(String, "/robot/response", 10)
        self.pub_say = self.create_publisher(String, "/robot/say", 10)
        self.create_timer(2.0, self.tick)
        self.state = 0

    def tick(self):
        moods = ["calm", "happy", "supportive"]
        mood = moods[self.state % len(moods)]
        self.state += 1
        e = String()
        e.data = mood
        r = String()
        r.data = f"Detected mood: {mood}"
        s = String()
        s.data = "I am here with you."
        self.pub_emotion.publish(e)
        self.pub_response.publish(r)
        self.pub_say.publish(s)


def main():
    rclpy.init()
    node = RobotPipelineNode()
    rclpy.spin(node)
    node.destroy_node()
    rclpy.shutdown()
