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
    # Получаем путь к пакету
    pkg_test_robot = get_package_share_directory('test_robot')
    
    # === НАСТРОЙКА ПУТЕЙ ===
    
    # 1. Путь к Xacro
    urdf_path = os.path.join(pkg_test_robot, 'urdf', 'model_xacro.xacro')

    rviz_config_path = os.path.join(pkg_test_robot, 'rviz', 'lidar.rviz')
    
    # 3. Путь к файлу МИРА (теперь он лежит в urdf папке)
    world_path = os.path.join(pkg_test_robot, 'urdf', 'world.sdf')
    
    robot_desc = ParameterValue(Command(['xacro ', urdf_path]), value_type=str)

    gz_sim = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            os.path.join(get_package_share_directory('ros_gz_sim'), 'launch', 'gz_sim.launch.py')),
        launch_arguments={'gz_args': f"-r {world_path}"}.items(),
    )

    # Спавн робота
    create = Node(
        package='ros_gz_sim',
        executable='create',
        arguments=['-name', 'robot',
                   '-topic', 'robot_description',
                   '-x', '0.0',
                   '-y', '0.0',
                   '-z', '0.5', # Поднимаем повыше при спавне
                ],
        output='screen',
    )

    # Robot State Publisher
    robot_state_publisher = Node(
        package='robot_state_publisher',
        executable='robot_state_publisher',
        name='robot_state_publisher',
        output='both',
        parameters=[
            {'robot_description': robot_desc},
            {'use_sim_time': True} # Важно для синхронизации
        ]
    )
    
    # RViz2
    rviz = Node(
       package='rviz2',
       executable='rviz2',
       arguments=['-d', rviz_config_path],
       condition=IfCondition(LaunchConfiguration('rviz')),
       parameters=[{'use_sim_time': True}]
    )

    # === МОСТ (BRIDGE) ===
    bridge = Node(
        package='ros_gz_bridge',
        executable='parameter_bridge',
        arguments=[
            # --- СТАРЫЕ (Робот и Лидар) ---
            '/joint_states@sensor_msgs/msg/JointState[gz.msgs.Model',
            '/lidar/raw@sensor_msgs/msg/LaserScan[gz.msgs.LaserScan', 
            '/model/robot/tf@tf2_msgs/msg/TFMessage[gz.msgs.Pose_V',
            '/clock@rosgraph_msgs/msg/Clock[gz.msgs.Clock',
            '/cmd_vel@geometry_msgs/msg/Twist]gz.msgs.Twist',
            '/camera/depth@sensor_msgs/msg/Image[gz.msgs.Image',
            '/camera/camera_info@sensor_msgs/msg/CameraInfo[gz.msgs.CameraInfo',
            '/imu/raw@sensor_msgs/msg/Imu[gz.msgs.IMU',
        ],
        remappings=[
            ('/lidar/raw', '/scan'),
            ('/model/robot/tf', '/tf'),
            ('/camera/depth', '/depth/image_raw'),
            ('/camera/camera_info', '/depth/camera_info'),
            ('/imu/raw', '/imu/data'),
        ],
        output='screen',
        parameters=[{'use_sim_time': True}]
    )
    
    lidar_tf = Node(
        package='tf2_ros',
        executable='static_transform_publisher',
        name='lidar_tf',
        arguments=['0', '0', '0', '0', '0', '0', 'lidar_link', 'robot/head/lidar_sensor'],
    )
    
   
    camera_tf = Node(
        package='tf2_ros',
        executable='static_transform_publisher',
        name='camera_tf',
        arguments=[
            '0', '0', '0', '0', '0', '0',
            'camera_link',
            'robot/head/depth_camera'
        ]
    )

    imu_tf = Node(
        package='tf2_ros',
        executable='static_transform_publisher',
        name='imu_tf',
        arguments=[
            '0', '0', '0', '0', '0', '0',
            'imu_link',
            'robot/base_link/imu_sensor'
        ]
    )
    
    return LaunchDescription([
        # Аргументы
        DeclareLaunchArgument('rviz', default_value='true',
                            description='Open RViz.'),
        DeclareLaunchArgument('teleop', default_value='true',
                            description='Launch rqt_steering for controlling the robot'),
        
        # Основные узлы
        gz_sim,
        robot_state_publisher,
        bridge,
        lidar_tf,
        camera_tf,
        imu_tf,
        # Таймеры
        TimerAction(
            period=3.0,
            actions=[create]),
            
        TimerAction(
            period=5.0,
            actions=[rviz]),
    ])
