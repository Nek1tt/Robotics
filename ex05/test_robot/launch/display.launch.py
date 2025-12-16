import os
from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, IncludeLaunchDescription, TimerAction
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration, Command
from launch_ros.actions import Node
from launch_ros.parameter_descriptions import ParameterValue

def generate_launch_description():
    pkg_test_robot = get_package_share_directory('test_robot')
    
    urdf_path = os.path.join(pkg_test_robot, 'urdf', 'model_xacro.xacro')
    # Можно использовать тот же конфиг rviz, главное добавить там DepthCloud вручную,
    # либо создать отдельный конфиг. Пока используем старый.
    rviz_config_path = os.path.join(pkg_test_robot, 'rviz', 'lidar.rviz') 
    world_path = os.path.join(pkg_test_robot, 'urdf', 'world.sdf')
    
    robot_desc = ParameterValue(Command(['xacro ', urdf_path]), value_type=str)

    # Gazebo
    gz_sim = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            os.path.join(get_package_share_directory('ros_gz_sim'), 'launch', 'gz_sim.launch.py')),
        launch_arguments={'gz_args': f"-r {world_path}"}.items(),
    )

    # Spawn (подальше от стены, на x=-2.0)
    create = Node(
        package='ros_gz_sim',
        executable='create',
        arguments=['-name', 'robot', '-topic', 'robot_description',
                   '-x', '-2.0', '-y', '0.0', '-z', '0.5'],
        output='screen',
    )

    # State Publisher
    robot_state_publisher = Node(
        package='robot_state_publisher',
        executable='robot_state_publisher',
        output='both',
        parameters=[{'robot_description': robot_desc}, {'use_sim_time': True}]
    )
    
    # RViz
    rviz = Node(
       package='rviz2',
       executable='rviz2',
       arguments=['-d', rviz_config_path],
       parameters=[{'use_sim_time': True}]
    )

    bridge = Node(
        package='ros_gz_bridge',
        executable='parameter_bridge',
        arguments=[
            '/joint_states@sensor_msgs/msg/JointState[gz.msgs.Model',
            '/lidar/raw@sensor_msgs/msg/LaserScan[gz.msgs.LaserScan',
            '/model/robot/tf@tf2_msgs/msg/TFMessage[gz.msgs.Pose_V',
            '/clock@rosgraph_msgs/msg/Clock[gz.msgs.Clock',
            # CMD_VEL (Twist, т.к. скрипт шлет Twist)
            '/cmd_vel@geometry_msgs/msg/Twist]gz.msgs.Twist',
            
            # КАМЕРА (Важно!)
            '/camera/depth@sensor_msgs/msg/Image[gz.msgs.Image',
            '/camera/camera_info@sensor_msgs/msg/CameraInfo[gz.msgs.CameraInfo',
        ],
        remappings=[
            ('/lidar/raw', '/scan'),
            ('/model/robot/tf', '/tf'),
            ('/model/robot/cmd_vel', '/cmd_vel'),
            ('/camera/depth', '/depth/image_raw'),
            ('/camera/camera_info', '/depth/camera_info'),
        ],
        output='screen',
        parameters=[{'use_sim_time': True}]
    )

    # Static TF
    lidar_tf = Node(
        package='tf2_ros',
        executable='static_transform_publisher',
        arguments=['0','0','0','0','0','0', 'lidar_link', 'robot/head/lidar_sensor']
    )

    depth_stop_node = Node(
        package='test_robot',
        executable='depth_stop',
        name='depth_stopper',
        output='screen',
        parameters=[{'use_sim_time': True}]
    )

    return LaunchDescription([
        gz_sim,
        robot_state_publisher,
        bridge,
        lidar_tf,
        
        TimerAction(period=3.0, actions=[create]),
        TimerAction(period=5.0, actions=[rviz]),
        
        # Запускаем мозг через 8 секунд
        TimerAction(period=8.0, actions=[depth_stop_node]),
    ])
