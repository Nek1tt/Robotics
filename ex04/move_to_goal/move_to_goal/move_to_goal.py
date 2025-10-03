import sys
import math
import rclpy
from rclpy.node import Node
from geometry_msgs.msg import Twist
from turtlesim.msg import Pose


class MoveToGoalNode(Node):
    def __init__(self, goal_x: float, goal_y: float, goal_theta: float):
        super().__init__('move_to_goal')
        self.goal_x = float(goal_x)
        self.goal_y = float(goal_y)
        self.goal_theta = float(goal_theta)

        # Publisher to cmd_vel
        self.pub = self.create_publisher(Twist, '/turtle1/cmd_vel', 10)
        # Subscriber to pose
        self.sub = self.create_subscription(Pose, '/turtle1/pose', self.pose_cb, 10)

        # Control gains and thresholds
        self.k_rho = 1.5  # linear gain
        self.k_alpha = 6.0  # angular gain to orient while moving
        self.k_beta = -1.0  # angular gain to final orientation

        self.max_linear = 2.0
        self.max_angular = 6.0

        self.pos_tolerance = 0.05
        self.angle_tolerance = 0.05

        self.current_pose = None
        self.arrived_position = False
        self.arrived_orientation = False

        # done flag -> set True when goal reached to allow clean exit in main
        self.done = False

        # rotate-first threshold: if heading error too large, rotate in place first
        self.rotate_threshold = math.pi / 2.0  # 90 degrees (tune if needed)

        # a short timer to ensure we re-check stop state and republish stop once done
        self._timer = self.create_timer(0.1, self._timer_cb)

        self.get_logger().info(f'move_to_goal: goal=({self.goal_x:.3f}, {self.goal_y:.3f}, {self.goal_theta:.3f})')

    def _timer_cb(self):
        # If done, ensure we publish stop (once). Do NOT call rclpy.shutdown() here.
        if self.done:
            stop = Twist()
            self.pub.publish(stop)
            # cancel timer to avoid repeated calls
            try:
                self._timer.cancel()
            except Exception:
                pass
            # do not shutdown here — main will observe node.done and shutdown cleanly

    def pose_cb(self, msg: Pose):
        self.current_pose = msg
        self.control_step()

    def normalize_angle(self, ang: float):
        while ang > math.pi:
            ang -= 2.0 * math.pi
        while ang < -math.pi:
            ang += 2.0 * math.pi
        return ang

    def control_step(self):
        if self.current_pose is None:
            return

        # pose fields: x,y,theta,linear_velocity,angular_velocity
        dx = self.goal_x - self.current_pose.x
        dy = self.goal_y - self.current_pose.y
        rho = math.hypot(dx, dy)

        # angle from turtle to goal in world frame
        angle_to_goal = math.atan2(dy, dx)

        # alpha: angle difference between heading and direction to goal
        alpha = self.normalize_angle(angle_to_goal - self.current_pose.theta)
        # beta: angle difference between desired final heading and direction to goal
        beta = self.normalize_angle(self.goal_theta - angle_to_goal)

        twist = Twist()

        # If not at position, drive towards it
        if rho > self.pos_tolerance:
            # Proportional controller (unicycle transform)
            linear = self.k_rho * rho
            angular = self.k_alpha * alpha + self.k_beta * beta

            # ---- rotate-first remains, but DO allow backward motion ----
            if abs(alpha) > self.rotate_threshold:
                linear = 0.0
                angular = max(-self.max_angular, min(self.max_angular, self.k_alpha * alpha))
            else:
                # allow backward motion: keep linear possibly negative
                linear = max(-self.max_linear, min(self.max_linear, linear))
                angular = max(-self.max_angular, min(self.max_angular, angular))

            twist.linear.x = linear
            twist.angular.z = angular
            self.arrived_position = False
            self.arrived_orientation = False
        else:
            # close enough to position: now correct orientation
            self.arrived_position = True
            angle_error = self.normalize_angle(self.goal_theta - self.current_pose.theta)
            if abs(angle_error) > self.angle_tolerance:
                twist.linear.x = 0.0
                twist.angular.z = max(-self.max_angular, min(self.max_angular, 3.0 * angle_error))
                self.arrived_orientation = False
            else:
                twist.linear.x = 0.0
                twist.angular.z = 0.0
                self.arrived_orientation = True

        self.pub.publish(twist)

        # log arrival once
        if self.arrived_position and self.arrived_orientation and not self.done:
            # log first
            self.get_logger().info('Arrived at goal. Stopping and shutting down.')
            # stop the turtle (the timer will re-publish once more)
            stop = Twist()
            self.pub.publish(stop)
            # mark done — main will detect this and exit the spin loop
            self.done = True


def main(argv=None):
    rclpy.init(args=argv)

    # parse args and validate ranges
    args = sys.argv[1:]
    if len(args) < 3:
        print('Usage: ros2 run move_to_goal move_to_goal X Y THETA')
        sys.exit(1)
    try:
        gx = float(args[0])
        gy = float(args[1])
        gth = float(args[2])
    except ValueError:
        print('Invalid numeric arguments.')
        sys.exit(1)

    # bounds for turtlesim
    if not (0.0 <= gx <= 11.0 and 0.0 <= gy <= 11.0):
        print('X and Y must be in range [0.0, 11.0]')
        sys.exit(1)
    if not (-math.pi <= gth <= math.pi):
        print('THETA must be in range [-pi, pi]')
        sys.exit(1)

    node = MoveToGoalNode(gx, gy, gth)

    try:
        while rclpy.ok() and not node.done:
            rclpy.spin_once(node, timeout_sec=0.1)
    except KeyboardInterrupt:
        pass
    finally:
        try:
            stop = Twist()
            node.pub.publish(stop)
        except Exception:
            pass
        try:
            node.destroy_node()
        except Exception:
            pass
        try:
            rclpy.shutdown()
        except Exception:
            pass

    sys.exit(0)


if __name__ == '__main__':
    main()

