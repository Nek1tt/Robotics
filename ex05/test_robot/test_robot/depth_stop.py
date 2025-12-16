#!/usr/bin/env python3
import rclpy
from rclpy.node import Node
from sensor_msgs.msg import Image
from geometry_msgs.msg import Twist
import numpy as np


class DepthStop(Node):
    def __init__(self):
        super().__init__('depth_stop')

        # Подписываемся на картинку глубины
        # Используем топик, который мы настроили ранее
        self.subscription = self.create_subscription(
            Image,
            '/depth/image_raw',
            self.depth_callback,
            10)

        self.publisher_ = self.create_publisher(Twist, '/cmd_vel', 10)

        self.stop_distance = 1.0  # Метры
        self.move_speed = 0.5

    def depth_callback(self, msg):
        # 1. Проверяем формат. Нам нужен 32-битный float (расстояние в метрах)
        if msg.encoding != '32FC1':
            # Gazebo часто шлет просто "float32" или "R_FLOAT32", обработаем это
            pass

            # 2. Конвертируем сырые байты в массив NumPy
        # msg.data - это список байтов. Мы говорим: "Читай каждые 4 байта как float32"
        depth_array = np.frombuffer(msg.data, dtype=np.float32)

        # 3. Превращаем одномерный массив в 2D картинку (высота x ширина)
        current_frame = depth_array.reshape((msg.height, msg.width))

        # 4. Вырезаем центр картинки (Region of Interest - ROI)
        # Нам не интересно, что по краям, нам важно, что прямо по курсу.
        height, width = current_frame.shape
        roi_size = 50  # Размер квадрата в центре (50x50 пикселей)

        center_y = height // 2
        center_x = width // 2

        # Берем срез массива
        roi = current_frame[center_y - roi_size: center_y + roi_size,
        center_x - roi_size: center_x + roi_size]

        # 5. Ищем минимальное расстояние в этом квадрате
        # Заменяем 'inf' (бесконечность) и 'nan' на большие числа, чтобы не ломать min()
        roi = np.nan_to_num(roi, posinf=100.0, nan=100.0)

        if roi.size > 0:
            min_dist = np.min(roi)
        else:
            min_dist = 100.0

        # 6. Логика движения
        cmd = Twist()

        if min_dist < self.stop_distance:
            cmd.linear.x = 0.0
            self.get_logger().info(f'Wall detected at {min_dist:.2f}m. Stop!', throttle_duration_sec=0.5)
        else:
            cmd.linear.x = self.move_speed
            self.get_logger().info(f'Clear ({min_dist:.2f}m). Go!', throttle_duration_sec=0.5)

        self.publisher_.publish(cmd)


def main(args=None):
    rclpy.init(args=args)
    node = DepthStop()
    rclpy.spin(node)
    node.destroy_node()
    rclpy.shutdown()


if __name__ == '__main__':
    main()