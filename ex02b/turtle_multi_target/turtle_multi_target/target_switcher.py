import rclpy
import math
from rclpy.node import Node
from tf2_ros import TransformBroadcaster
from geometry_msgs.msg import TransformStamped
from turtlesim.srv import Spawn


class TargetSwitcher(Node):
    def __init__(self):
        super().__init__('target_swithcer')
        self.tf_broadcaster = TransformBroadcaster(self)
        self.spawner = self.create_client(Spawn, 'spawn')
        # Boolean values to store the information
        # if the service for spawning turtle is available
        self.turtle_spawning_service_ready = False
        # if the turtle was successfully spawned
        self.turtle_spawned = False
        self.timer1 = self.create_timer(0.02, lambda: self.static_broadcast_timer_callback('turtle1', 'carrot1'))
        self.timer2 = self.create_timer(0.02, lambda: self.static_broadcast_timer_callback('turtle3', 'carrot2'))
        self.timer3 = self.create_timer(0.02, lambda: self.static_broadcast_timer_callback('world', 'static_target'))

    
    def dynamic_broadcast_timer_callback(self, parent, child):
        if self.turtle_spawning_service_ready:
            if self.turtle_spawned:
                now = self.get_clock().now().nanoseconds / 1e9  
                x = now
                x = x + math.pi
                t = TransformStamped()
                t.header.stamp = self.get_clock().now().to_msg()
                t.header.frame_id = parent
                t.child_frame_id = child
                t.transform.translation.x = 3*math.sin(x)
                t.transform.translation.y = 3*math.cos(x)
                t.transform.translation.z = 0.0
                t.transform.rotation.x = 0.0
                t.transform.rotation.y = 0.0
                t.transform.rotation.z = 0.0
                t.transform.rotation.w = 1.0
                self.tf_broadcaster.sendTransform(t)
            else:
                if self.result.done():
                    self.get_logger().info(
                        f'Successfully spawned {self.result.result().name}')
                    self.turtle_spawned = True
                else:
                    self.get_logger().info('Spawn is not finished')
        else:
            if self.spawner.service_is_ready():
                request = Spawn.Request()
                request.name = 'turtle3'
                request.x = 7.0
                request.y = -3.0
                request.theta = 0.0
                self.result = self.spawner.call_async(request)
                self.turtle_spawning_service_ready = True
            else:
                self.get_logger().info('Service is not ready')

    def static_broadcast_timer_callback(self, parent, child):
        if self.turtle_spawning_service_ready:
            if self.turtle_spawned:
                t = TransformStamped()

                t.header.stamp = self.get_clock().now().to_msg()
                t.header.frame_id = parent
                t.child_frame_id = child
                t.transform.translation.x = 2.0
                t.transform.translation.y = 2.0
                t.transform.translation.z = 0.0
                t.transform.rotation.x = 0.0
                t.transform.rotation.y = 0.0
                t.transform.rotation.z = 0.0
                t.transform.rotation.w = 1.0

                self.tf_broadcaster.sendTransform(t)
            else:
                if self.result.done():
                    self.get_logger().info(
                        f'Successfully spawned {self.result.result().name}')
                    self.turtle_spawned = True
                else:
                    self.get_logger().info('Spawn is not finished')
        else:
            if self.spawner.service_is_ready():
                request = Spawn.Request()
                request.name = 'turtle3'
                request.x = 7.0
                request.y = -3.0
                request.theta = 0.0
                self.result = self.spawner.call_async(request)
                self.turtle_spawning_service_ready = True
            else:
                self.get_logger().info('Service is not ready')


def main():
    rclpy.init()
    node = TargetSwitcher()
    try:
        rclpy.spin(node)

    except KeyboardInterrupt:
        pass

    rclpy.shutdown()
