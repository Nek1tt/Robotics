#!/usr/bin/env python3
import math
import rclpy
from rclpy.node import Node
from rclpy.action import ActionServer
from geometry_msgs.msg import Twist
from turtlesim.msg import Pose
from action_cleaning_robot.action import CleaningTask
import time

class CleaningActionServer(Node):
    def __init__(self):
        super().__init__('cleaning_action_server')

        self.cmd_pub = self.create_publisher(Twist, '/turtle1/cmd_vel', 10)
        self.pose_sub = self.create_subscription(Pose, '/turtle1/pose', self.pose_cb, 10)
        self.current_pose = None

        self._action_server = ActionServer(
            self,
            CleaningTask,
            'cleaning_action',
            self.execute_callback
        )

        self.pos_tol = 0.05
        self.rate_hz = 10.0
        self.k_rho = 1.5
        self.k_alpha = 6.0
        self.max_linear = 2.0
        self.max_angular = 6.0

    def pose_cb(self, msg: Pose):
        self.current_pose = msg

    def _publish_twist(self, linear, angular):
        t = Twist()
        t.linear.x = linear
        t.angular.z = angular
        self.cmd_pub.publish(t)

    def move_to(self, x_target, y_target, goal_handle=None, task=None, initial_dist_for_return=None, cleaned_so_far=0, total_grid_points=1):
        # wait for pose
        wait_t0 = time.time()
        while self.current_pose is None and time.time() - wait_t0 < 3.0:
            rclpy.spin_once(self, timeout_sec=0.05)

        if self.current_pose is None:
            self.get_logger().warning('No pose available to move.')
            return 0.0

        # initialize
        prev_x = self.current_pose.x
        prev_y = self.current_pose.y
        dist_sum = 0.0

        # compute initial distance for return_home feedback if not provided
        if goal_handle is not None and task == 'return_home':
            dx0 = x_target - self.current_pose.x
            dy0 = y_target - self.current_pose.y
            initial = initial_dist_for_return if initial_dist_for_return is not None else math.hypot(dx0, dy0)
            # avoid zero division
            if initial <= 1e-6:
                initial = 1e-6
        else:
            initial = None

        # control loop
        while rclpy.ok():
            if goal_handle is not None and goal_handle.is_cancel_requested:
                goal_handle.canceled()
                # stop
                self._publish_twist(0.0, 0.0)
                return dist_sum

            dx = x_target - self.current_pose.x
            dy = y_target - self.current_pose.y
            rho = math.hypot(dx, dy)
            if rho <= self.pos_tol:
                # reached
                self._publish_twist(0.0, 0.0)
                break

            angle_to_goal = math.atan2(dy, dx)
            alpha = angle_to_goal - self.current_pose.theta
            # normalize angle to [-pi, pi]
            alpha = (alpha + math.pi) % (2.0 * math.pi) - math.pi

            # P-control
            linear = self.k_rho * rho
            angular = self.k_alpha * alpha

            # saturate
            linear = max(-self.max_linear, min(self.max_linear, linear))
            angular = max(-self.max_angular, min(self.max_angular, angular))

            self._publish_twist(linear, angular)

            # spin once, then measure step distance
            rclpy.spin_once(self, timeout_sec=1.0 / self.rate_hz)

            # accumulate step distance
            if self.current_pose is not None:
                step = math.hypot(self.current_pose.x - prev_x, self.current_pose.y - prev_y)
                dist_sum += step
                prev_x = self.current_pose.x
                prev_y = self.current_pose.y

            # if request is return_home — publish periodic feedback based on remaining rho
            if goal_handle is not None and task == 'return_home' and initial is not None:
                perc = int(max(0, min(100, (1.0 - rho / initial) * 100)))
                fb = CleaningTask.Feedback()
                fb.progress_percent = perc
                fb.current_cleaned_points = cleaned_so_far
                fb.current_x = self.current_pose.x
                fb.current_y = self.current_pose.y
                goal_handle.publish_feedback(fb)
                # also log on server
                self.get_logger().info(f'Feedback: {fb.progress_percent}% cleaned, {fb.current_cleaned_points} points, current position=({fb.current_x:.2f}, {fb.current_y:.2f})')

        # final stop (ensure velocity zero)
        self._publish_twist(0.0, 0.0)

        # final feedback on arrival for return_home
        if goal_handle is not None and task == 'return_home':
            fb = CleaningTask.Feedback()
            fb.progress_percent = 100
            fb.current_cleaned_points = cleaned_so_far
            fb.current_x = self.current_pose.x
            fb.current_y = self.current_pose.y
            goal_handle.publish_feedback(fb)
            self.get_logger().info(f'Feedback: {fb.progress_percent}% cleaned, {fb.current_cleaned_points} points, current position=({fb.current_x:.2f}, {fb.current_y:.2f})')

        return dist_sum

    def execute_callback(self, goal_handle):
        """Main action handler. Supports 'clean_square' and 'return_home'."""
        self.get_logger().info(f"Goal arrived: task={goal_handle.request.task_type}, area_size={goal_handle.request.area_size}, target_x={goal_handle.request.target_x}, target_y={goal_handle.request.target_y}")
    
        cleaned_points = 0
        total_distance = 0.0

        # ensure we have pose
        wait_t0 = time.time()
        while self.current_pose is None and time.time() - wait_t0 < 3.0:
            rclpy.spin_once(self, timeout_sec=0.05)

        start_x = self.current_pose.x if self.current_pose else 5.5
        start_y = self.current_pose.y if self.current_pose else 5.5

        task = goal_handle.request.task_type
        area_size = goal_handle.request.area_size

        if task == 'clean_square':
            # grid parameters
            step_size = 1.0
            num_steps = max(1, int(round(area_size / step_size)))

            # assemble grid points in a zig-zag order
            grid_points = []
            for i in range(num_steps):
                # y coordinate for this row
                y = start_y + i * step_size
                if i % 2 == 0:
                    x_iter = range(num_steps)
                else:
                    x_iter = reversed(range(num_steps))
                for j in x_iter:
                    x = start_x + j * step_size
                    grid_points.append((x, y))

            total_cells = len(grid_points)
            # iterate all grid points; count only these as cleaned points
            for idx, (xg, yg) in enumerate(grid_points):
                # move to grid point AND do not publish return_home-style feedback here
                d = self.move_to(xg, yg, goal_handle=None, task=None)
                total_distance += d
                cleaned_points += 1

                # publish feedback after arrival at grid cell
                fb = CleaningTask.Feedback()
                perc = int(cleaned_points / total_cells * 100)
                fb.progress_percent = max(0, min(100, perc))
                fb.current_cleaned_points = cleaned_points
                fb.current_x = self.current_pose.x
                fb.current_y = self.current_pose.y
                goal_handle.publish_feedback(fb)
                self.get_logger().info(f'Feedback: {fb.progress_percent}% cleaned, {fb.current_cleaned_points} points, current position=({fb.current_x:.2f}, {fb.current_y:.2f})')

            # after finishing grid, return to start (do not increment cleaned_points for this return)
            d = self.move_to(start_x, start_y, goal_handle=None, task=None)
            total_distance += d

        elif task == 'return_home':
            # compute initial distance for feedback inside move_to
            tx = goal_handle.request.target_x
            ty = goal_handle.request.target_y
            dx0 = tx - self.current_pose.x
            dy0 = ty - self.current_pose.y
            initial = math.hypot(dx0, dy0)
            # call move_to with goal_handle so it publishes periodic feedback for return_home
            d = self.move_to(tx, ty, goal_handle=goal_handle, task='return_home', initial_dist_for_return=initial, cleaned_so_far=cleaned_points)
            total_distance += d
            # cleaned_points remains as is (return_home doesn't add cleaned points)

        else:
            self.get_logger().warning(f'Unknown task type: {task}')
            goal_handle.abort()
            result = CleaningTask.Result()
            result.success = False
            result.cleaned_points = cleaned_points
            result.total_distance = total_distance
            return result

        # finish goal
        goal_handle.succeed()
        result = CleaningTask.Result()
        result.success = True
        result.cleaned_points = cleaned_points
        result.total_distance = total_distance
        self.get_logger().info(f'Task finished: success={result.success}, cleaned_points={result.cleaned_points}, total_distance={result.total_distance:.2f}')
        return result

def main(args=None):
    rclpy.init(args=args)
    node = CleaningActionServer()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()

if __name__ == '__main__':
    main()
