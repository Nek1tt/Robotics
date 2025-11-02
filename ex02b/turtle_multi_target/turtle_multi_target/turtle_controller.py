# Copyright 2021 Open Source Robotics Foundation, Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import math

from geometry_msgs.msg import Twist

import rclpy
from rclpy.node import Node

from tf2_ros import TransformException
from tf2_ros.buffer import Buffer
from tf2_ros.transform_listener import TransformListener
from target_interface.msg import Interface

from turtlesim.srv import Spawn
from turtlesim.msg import Pose
import threading



class FrameListener(Node):

    def __init__(self):
        super().__init__('turtle_tf2_frame_listener')

        # Declare and acquire `target_frame` parameter
        self.target_frame = self.declare_parameter(
            'target_frame', 'carrot1').get_parameter_value().string_value

        self.tf_buffer = Buffer()
        self.tf_listener = TransformListener(self.tf_buffer, self)

        # Create a client to spawn a turtle
        self.spawner = self.create_client(Spawn, 'spawn')
        # Boolean values to store the information
        # if the service for spawning turtle is available
        self.turtle_spawning_service_ready = False
        # if the turtle was successfully spawned
        self.turtle_spawned = False

        # Create turtle2 velocity publisher
        self.publisher = self.create_publisher(Twist, 'turtle2/cmd_vel', 1)
        self.publisher_target = self.create_publisher(Interface, '/current_target', 1)
        self.subscription = None
        
        self.pose_msg = None
        # Call on_timer function every second
        self.timer = self.create_timer(1.0, self.on_timer)
        self.current_active = 0
        self.targets = ['carrot1','carrot2', 'static_target']
        self.switch_threshold = self.declare_parameter('switch_threshold', 1.0).get_parameter_value().double_value
        threading.Thread(target=self.keyboard_listener, daemon=True).start()


    def on_timer(self):
        # Store frame names in variables that will be used to
        # compute transformations
        from_frame_rel = self.target_frame
        to_frame_rel = 'turtle2'

        if self.turtle_spawning_service_ready:
            if self.turtle_spawned:
                # Look up for the transformation between target_frame and turtle2 frames
                # and send velocity commands for turtle2 to reach target_frame
                try:
                    t = self.tf_buffer.lookup_transform(
                        to_frame_rel,
                        from_frame_rel,
                        rclpy.time.Time())
                except TransformException as ex:
                    self.get_logger().info(
                        f'Could not transform {to_frame_rel} to {from_frame_rel}: {ex}')
                    return

                msg = Twist()
                scale_rotation_rate = 1.0
                msg.angular.z = scale_rotation_rate * math.atan2(
                    t.transform.translation.y,
                    t.transform.translation.x)

                scale_forward_speed = 0.8
                msg.linear.x = scale_forward_speed * math.sqrt(
                    t.transform.translation.x ** 2 +
                    t.transform.translation.y ** 2)

                self.publisher.publish(msg)
                distance = math.sqrt(t.transform.translation.x**2 + t.transform.translation.y**2)
                msg2 = Interface()
                msg2.target_name = self.target_frame
                msg2.target_x = t.transform.translation.x
                msg2.target_y = t.transform.translation.y
                msg2.distance_to_target = distance

                self.publisher_target.publish(msg2)
                if distance < self.switch_threshold:
                    self.current_active += 1
                    self.target_frame = self.targets[self.current_active % len(self.targets)]
                    self.get_logger().info(f'Switched target to: {self.target_frame}')
                

            else:
                if self.result.done():
                    self.get_logger().info(
                        f'Successfully spawned {self.result.result().name}')
                    self.turtle_spawned = True
                    self.subscription = self.create_subscription(
                            Pose,
                            '/turtle2/pose',
                            self.handle_turtle_pose,
                            1)
                else:
                    self.get_logger().info('Spawn is not finished')
        else:
            if self.spawner.service_is_ready():
                # Initialize request with turtle name and coordinates
                # Note that x, y and theta are defined as floats in turtlesim/srv/Spawn
                request = Spawn.Request()
                request.name = 'turtle2'
                request.x = 4.0
                request.y = 2.0
                request.theta = 0.0
                # Call request
                self.result = self.spawner.call_async(request)
                self.turtle_spawning_service_ready = True
            else:
                # Check if the service is ready
                self.get_logger().info('Service is not ready')

    def handle_turtle_pose(self, msg):
        self.pose_msg = msg

    def keyboard_listener(self):
        while True:
            key = input()
            if key.lower() == 'n':
                # Переключаем цель
                self.current_active += 1
                self.target_frame = self.targets[self.current_active % len(self.targets)]
                self.get_logger().info(f'Switched target to: {self.target_frame}')

def main():
    rclpy.init()
    node = FrameListener()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass

    rclpy.shutdown()
