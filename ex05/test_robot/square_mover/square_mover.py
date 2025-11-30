#!/usr/bin/env python3
import rclpy
from rclpy.node import Node
from geometry_msgs.msg import Twist
from std_msgs.msg import Float64
import math


class SquareDriver(Node):
    def __init__(self):
        super().__init__('square_driver')

        # Публикаторы для движения
        self.cmd_vel_pub = self.create_publisher(Twist, '/cmd_vel', 10)

        self.head_pub = self.create_publisher(Float64, '/head_swivel_cmd', 10)
        self.gripper_extension_pub = self.create_publisher(Float64, '/gripper_extension_cmd', 10)
        self.left_gripper_pub = self.create_publisher(Float64, '/left_gripper_cmd', 10)
        self.right_gripper_pub = self.create_publisher(Float64, '/right_gripper_cmd', 10)

        self.timer = self.create_timer(0.1, self.timer_callback)  # 10 Гц

        self.square_state = 0
        self.state_timer = 0

        self.head_angle = 0.0
        self.gripper_extended = False
        self.gripper_open = False

        self.get_logger().info('Square driver started!')

    def timer_callback(self):
        # 1. Управление движением по квадрату
        self.control_square_movement()

        # 2. Управление головой (вращение)
        self.control_head()

        # 3. Управление манипулятором
        self.control_manipulator()

        self.state_timer += 1

    def control_square_movement(self):
        msg = Twist()

        if self.square_state in [0, 2, 4, 6]:  # Движение вперед
            if self.state_timer < 40:  # 4 секунды
                msg.linear.x = 0.5
                msg.angular.z = 0.0
            else:
                self.state_timer = 0
                self.square_state += 1  # Переход к повороту
        else:  # Поворот
            if self.state_timer < 30:
                msg.linear.x = 0.1
                msg.angular.z = 1.57
            else:
                self.state_timer = 0
                self.square_state = (self.square_state + 1) % 8

        self.cmd_vel_pub.publish(msg)

    def control_head(self):
        head_msg = Float64()
        self.head_angle = (self.head_angle + 0.1) % (2 * math.pi)
        head_msg.data = math.sin(self.head_angle) * 2.0
        self.head_pub.publish(head_msg)

    def control_manipulator(self):
        cycle_time = self.state_timer % 80  # 8-секундный цикл

        # Управление выдвижением манипулятора
        extension_msg = Float64()
        if cycle_time < 40:  # Первые 4 секунды - выдвинут
            extension_msg.data = 0.0  # Полностью выдвинут
            self.gripper_extended = True
        else:  # Следующие 4 секунды - задвинут
            extension_msg.data = -0.2  # Частично задвинут
            self.gripper_extended = False
        self.gripper_extension_pub.publish(extension_msg)

        # Управление пальцами захвата
        gripper_msg = Float64()
        if cycle_time < 20 or (cycle_time >= 40 and cycle_time < 60):
            gripper_msg.data = 0.0  # Открыт
            self.gripper_open = True
        else:
            gripper_msg.data = 0.3  # Закрыт
            self.gripper_open = False

        self.left_gripper_pub.publish(gripper_msg)
        self.right_gripper_pub.publish(gripper_msg)

        if self.state_timer % 20 == 0:
            self.get_logger().info(f'Head: {self.head_angle:.2f}, '
                                   f'Gripper extended: {self.gripper_extended}, '
                                   f'Gripper open: {self.gripper_open}')


def main(args=None):
    rclpy.init(args=args)
    node = SquareDriver()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        stop_msg = Twist()
        node.cmd_vel_pub.publish(stop_msg)
        node.get_logger().info('Square driver stopped')
        node.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()