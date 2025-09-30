import rclpy
from rclpy.node import Node
from geometry_msgs.msg import Twist
from std_msgs.msg import String

class TextToCmdVel(Node):
    def __init__(self):
        super().__init__('text_to_cmd_vel')
        
        self.cmd_vel_publisher = self.create_publisher(
            Twist, 
            '/turtle1/cmd_vel', 
            10
        )

        self.text_subscriber = self.create_subscription(
            String,
            'cmd_text',
            self.text_callback,
            10
        )
        
        self.get_logger().info('Text to cmd_vel node started')
    
    def text_callback(self, msg):
        command = msg.data.lower().strip()
        twist_msg = Twist()
        
        if command == "turn_right":
            twist_msg.angular.z = -1.5
            self.get_logger().info(f'Command received: {command} - turning right')
            
        elif command == "turn_left":
            twist_msg.angular.z = 1.5
            self.get_logger().info(f'Command received: {command} - turning left')
            
        elif command == "move_forward":
            twist_msg.linear.x = 1.0
            self.get_logger().info(f'Command received: {command} - moving forward')
            
        elif command == "move_backward":
            twist_msg.linear.x = -1.0
            self.get_logger().info(f'Command received: {command} - moving backward')
            
        else:
            self.get_logger().warn(f'Unknown command: {command}')
            return
        
        self.cmd_vel_publisher.publish(twist_msg)

def main(args=None):
    rclpy.init(args=args)
    node = TextToCmdVel()
    
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()

if __name__ == '__main__':
    main()
