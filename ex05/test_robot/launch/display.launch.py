# Copyright 2022 Open Source Robotics Foundation, Inc.
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

import os

from ament_index_python.packages import get_package_share_directory

from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, IncludeLaunchDescription
from launch.conditions import IfCondition
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration, Command
from launch_ros.parameter_descriptions import ParameterValue
from launch_ros.actions import Node
from launch.actions import TimerAction


def generate_launch_description():
    # Get package share directory
    pkg_test_robot = get_package_share_directory('test_robot')
    
    # Define paths using package share directory
    urdf_path = os.path.join(pkg_test_robot, 'urdf', 'model_xacro.xacro')
    rviz_config_path = os.path.join(pkg_test_robot, 'rviz', 'urdf.rviz')
    bridge_config_path = os.path.join(pkg_test_robot, 'config', 'model_bridge.yaml')
    
    robot_desc = ParameterValue(Command(['xacro ', urdf_path]), value_type=str)

    # Setup to launch the simulator and Gazebo world
    gz_sim = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            os.path.join(get_package_share_directory('ros_gz_sim'), 'launch', 'gz_sim.launch.py')),
        launch_arguments={'gz_args': "-r empty.sdf"}.items(),
    )

    # Spawn robot
    create = Node(
        package='ros_gz_sim',
        executable='create',
        arguments=['-name', 'robot',
                   '-topic', 'robot_description',
                   '-x', '0.0',
                   '-y', '0.0',
                   '-z', '0.3',
                ],
        output='screen',
    )

    # Robot state publisher
    robot_state_publisher = Node(
        package='robot_state_publisher',
        executable='robot_state_publisher',
        name='robot_state_publisher',
        output='both',
        parameters=[
            {'robot_description': robot_desc},
        ]
    )
    
    # Joint state publisher
    joint_state_publisher_node = Node(
        package='joint_state_publisher',
        executable='joint_state_publisher',
        name='joint_state_publisher',
        parameters=[{'robot_description': robot_desc}],
    )
    
    # RViz2
    rviz = Node(
       package='rviz2',
       executable='rviz2',
       arguments=['-d', rviz_config_path],
       condition=IfCondition(LaunchConfiguration('rviz'))
    )

    # Bridge
    bridge = Node(
        package='ros_gz_bridge',
        executable='parameter_bridge',
        parameters=[{
            'config_file': bridge_config_path,
            'qos_overrides./tf_static.publisher.durability': 'transient_local',
        }],
        output='screen'
    )
    

    return LaunchDescription([
        # Launch arguments
        DeclareLaunchArgument('rviz', default_value='true',
                            description='Open RViz.'),
        DeclareLaunchArgument('teleop', default_value='true',
                            description='Launch rqt_steering for controlling the robot'),
        
        # Main nodes
        gz_sim,
        robot_state_publisher,
        joint_state_publisher_node,
        bridge,
        
        # Timers for sequential startup
        TimerAction(
            period=3.0,
            actions=[create]),
            
        TimerAction(
            period=5.0,
            actions=[rviz]),
    ])
