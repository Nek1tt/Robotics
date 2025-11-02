import rclpy
import math
from rclpy.node import Node
from tf2_ros import TransformBroadcaster
from geometry_msgs.msg import TransformStamped


class CarrotFrameBroadcaster(Node):
    def __init__(self):
        super().__init__('carrot_frame_broadcaster')
        self.radius = self.declare_parameter('radius', 5.0).get_parameter_value().double_value
        self.direction = self.declare_parameter('direction_of_rotation', 1).get_parameter_value().integer_value
        self.tf_broadcaster = TransformBroadcaster(self)
        self.timer = self.create_timer(0.02, self.broadcast_timer_callback)

    
    def broadcast_timer_callback(self):
        now = self.get_clock().now().nanoseconds / 1e9  
        x = now


        x = self.direction*x + math.pi

        t = TransformStamped()

        t.header.stamp = self.get_clock().now().to_msg()
        t.header.frame_id = 'turtle1'
        t.child_frame_id = 'carrot1'
        t.transform.translation.x = self.radius*math.sin(x)
        t.transform.translation.y = self.radius*math.cos(x)
        t.transform.translation.z = 0.0
        t.transform.rotation.x = 0.0
        t.transform.rotation.y = 0.0
        t.transform.rotation.z = 0.0
        t.transform.rotation.w = 1.0

        self.tf_broadcaster.sendTransform(t)



def main():
    rclpy.init()
    node = CarrotFrameBroadcaster()
    try:
        rclpy.spin(node)

    except KeyboardInterrupt:
        pass

    rclpy.shutdown()
