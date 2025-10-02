import rclpy
from rclpy.node import Node
from full_name_interface.srv import FullNameSumService

class FullNameService(Node):
    def __init__(self):
        super().__init__('service_name')
        self.srv = self.create_service(FullNameSumService, 'SummFullName', self.full_name_callback)
        self.get_logger().info('FullName Service is ready...')

    def full_name_callback(self, request, response):
        full_name = f"{request.last_name}{request.name}{request.first_name}"
        response.full_name = full_name
        self.get_logger().info(f'Received: {request.last_name} {request.name} {request.first_name} -> {full_name}')
        return response

def main(args=None):
    rclpy.init(args=args)
    full_name_service = FullNameService()
    try:
        rclpy.spin(full_name_service)
    except KeyboardInterrupt:
        pass
    finally:
        full_name_service.destroy_node()
        rclpy.shutdown()

if __name__ == '__main__':
    main()
