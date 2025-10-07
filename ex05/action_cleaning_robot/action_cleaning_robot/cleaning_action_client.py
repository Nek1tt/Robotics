#!/usr/bin/env python3
import rclpy
from rclpy.node import Node
from action_cleaning_robot.action import CleaningTask
from rclpy.action import ActionClient

class CleaningClient(Node):
    def __init__(self):
        super().__init__('cleaning_action_client')
        self.client = ActionClient(self, CleaningTask, 'cleaning_action')

    def send_goal(self, task_type, area_size=0.0, target_x=0.0, target_y=0.0):
        self.get_logger().info(f'Sending goal: {task_type}')
        goal_msg = CleaningTask.Goal()
        goal_msg.task_type = task_type
        goal_msg.area_size = area_size
        goal_msg.target_x = target_x
        goal_msg.target_y = target_y

        goal_handle_future = self.client.send_goal_async(goal_msg)
        rclpy.spin_until_future_complete(self, goal_handle_future)
        goal_handle = goal_handle_future.result()

        if not goal_handle.accepted:
            self.get_logger().info('Goal rejected')
            return None

        self.get_logger().info('Goal accepted, waiting for result...')
        result_future = goal_handle.get_result_async()

        while not result_future.done():
            rclpy.spin_once(self, timeout_sec=0.1)

        result = result_future.result().result
        self.get_logger().info(f'Task finished: success={result.success}, '
                               f'cleaned_points={result.cleaned_points}, '
                               f'total_distance={result.total_distance:.2f}')
        return result

def main(args=None):
    rclpy.init(args=args)
    client = CleaningClient()
    
    client.send_goal('clean_square', area_size=6.0)

    client.send_goal('return_home', target_x=7.5, target_y=7.5)

    client.destroy_node()
    rclpy.shutdown()

if __name__ == '__main__':
    main()

