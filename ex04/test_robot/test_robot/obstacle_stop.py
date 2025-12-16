#!/usr/bin/env python3
import rclpy
from rclpy.node import Node
from sensor_msgs.msg import LaserScan
from geometry_msgs.msg import Twist

class ObstacleStop(Node):
    def __init__(self):
        super().__init__('obstacle_stop')
        
        # Подписываемся на лидар
        self.subscription = self.create_subscription(
            LaserScan,
            '/scan',
            self.scan_callback,
            10)
            
        # Публикуем команды скорости (стандартный Twist)
        self.publisher_ = self.create_publisher(Twist, '/cmd_vel', 10)
        
        # Параметры
        self.stop_distance = 1.0  # Остановиться за 1 метр
        self.move_speed = 0.5     # Скорость движения (м/с)

    def scan_callback(self, msg):
        # min_angle = -3.14 (Сзади), max_angle = 3.14 (Сзади).
        # Значит, 0 градусов (Прямо по курсу) находится в середине массива.
        
        # Берем центральный сектор (например, 20 градусов перед роботом)
        # Индекс 180 - это центр. Берем от 170 до 190.
        mid_index = len(msg.ranges) // 2
        window_size = 10 
        
        # Вырезаем сектор перед роботом
        front_ranges = msg.ranges[mid_index - window_size : mid_index + window_size]
        
        # Фильтруем "inf" (бесконечность), заменяя их на большое число
        valid_ranges = [r if r != float('inf') else 100.0 for r in front_ranges]
        
        # Находим минимальное расстояние в этом секторе
        if len(valid_ranges) > 0:
            min_dist = min(valid_ranges)
        else:
            min_dist = 100.0 # Если данных нет, считаем что пусто
            
        # Логика движения
        cmd = Twist()
        
        if min_dist < self.stop_distance:
            # ПРЕПЯТСТВИЕ! СТОП!
            cmd.linear.x = 0.0
            cmd.angular.z = 0.0
            self.get_logger().info(f'Obstacle detected at {min_dist:.2f}m. Stopping!', throttle_duration_sec=1)
        else:
            # ПУТЬ СВОБОДЕН! ВПЕРЕД!
            cmd.linear.x = self.move_speed
            cmd.angular.z = 0.0
            self.get_logger().info(f'Path clear ({min_dist:.2f}m). Moving forward.', throttle_duration_sec=1)
            
        self.publisher_.publish(cmd)

def main(args=None):
    rclpy.init(args=args)
    node = ObstacleStop()
    rclpy.spin(node)
    node.destroy_node()
    rclpy.shutdown()

if __name__ == '__main__':
    main()
