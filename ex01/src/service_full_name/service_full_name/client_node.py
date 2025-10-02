import sys
import rclpy
from rclpy.node import Node
from full_name_interface.srv import FullNameSumService

class FullNameClient(Node):
    def __init__(self):
        super().__init__('client_name')
        self.cli = self.create_client(FullNameSumService, 'SummFullName')
        while not self.cli.wait_for_service(timeout_sec=1.0):
            self.get_logger().info('Service not available, waiting again...')

    def send_request(self, last_name, name, first_name):
        request = FullNameSumService.Request()
        request.last_name = last_name
        request.name = name
        request.first_name = first_name
        
        self.future = self.cli.call_async(request)
        rclpy.spin_until_future_complete(self, self.future)
        
        if self.future.result() is not None:
            return self.future.result().full_name
        else:
            self.get_logger().error('Service call failed')
            return None

def main(args=None):
    rclpy.init(args=args)
    if len(sys.argv) != 4:
        print("Usage: ros2 run service_full_name client_name <last_name> <name> <first_name>")
        return
    
    client = FullNameClient()
    result = client.send_request(sys.argv[1], sys.argv[2], sys.argv[3])
    
    if result:
        print(f"Full name: {result}")
    else:
        print("Failed to get full name")
    
    client.destroy_node()
    rclpy.shutdown()

if __name__ == '__main__':
    main()
