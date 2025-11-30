#!/usr/bin/env python3

import rclpy
from rclpy.node import Node
from geometry_msgs.msg import Twist
import math

class CircleDriver(Node):
    def __init__(self):
        super().__init__('circle_driver')
        self.pub = self.create_publisher(Twist, '/cmd_vel', 10)
        self.timer = self.create_timer(0.1, self.timer_callback)
        self.angle = 0.0

    def timer_callback(self):
        msg = Twist()
        msg.linear.x = 0.9
        msg.angular.z = 0.5
        self.pub.publish(msg)

def main(args=None):
    rclpy.init(args=args)
    node = CircleDriver()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.get_logger().info('Shutting down circle_driver...')
        node.destroy_node()
        rclpy.shutdown()

if __name__ == '__main__':
    main()
