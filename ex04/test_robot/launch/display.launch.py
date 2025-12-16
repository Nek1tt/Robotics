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
    
    # Пути
    urdf_path = os.path.join(pkg_test_robot, 'urdf', 'model_xacro.xacro')
    rviz_config_path = os.path.join(pkg_test_robot, 'rviz', 'lidar.rviz') # Используем конфиг с лидаром
    world_path = os.path.join(pkg_test_robot, 'urdf', 'world.sdf')
    
    robot_desc = ParameterValue(Command(['xacro ', urdf_path]), value_type=str)

    # 1. Gazebo Sim
    gz_sim = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            os.path.join(get_package_share_directory('ros_gz_sim'), 'launch', 'gz_sim.launch.py')),
        launch_arguments={'gz_args': f"-r {world_path}"}.items(),
    )

    # 2. Spawn Robot (Спавним подальше, чтобы было куда ехать)
    # x = -2.0, чтобы до стены (которая на x=2.5) было расстояние
    create = Node(
        package='ros_gz_sim',
        executable='create',
        arguments=['-name', 'robot',
                   '-topic', 'robot_description',
                   '-x', '-2.0', '-y', '0.0', '-z', '0.5',
                ],
        output='screen',
    )

    # 3. State Publishers
    robot_state_publisher = Node(
        package='robot_state_publisher',
        executable='robot_state_publisher',
        output='both',
        parameters=[{'robot_description': robot_desc}, {'use_sim_time': True}]
    )
    
    # 4. RViz
    rviz = Node(
       package='rviz2',
       executable='rviz2',
       arguments=['-d', rviz_config_path],
       parameters=[{'use_sim_time': True}]
    )

    # 5. Bridge (Мост)
    bridge = Node(
        package='ros_gz_bridge',
        executable='parameter_bridge',
        arguments=[
            # Joint States
            '/joint_states@sensor_msgs/msg/JointState[gz.msgs.Model',
            # Lidar
            '/lidar/raw@sensor_msgs/msg/LaserScan[gz.msgs.LaserScan',
            # TF / Clock
            '/model/robot/tf@tf2_msgs/msg/TFMessage[gz.msgs.Pose_V',
            '/clock@rosgraph_msgs/msg/Clock[gz.msgs.Clock',
            
            # CMD_VEL: Используем стандартный Twist для автопилота
            '/cmd_vel@geometry_msgs/msg/Twist]gz.msgs.Twist',
            
            # Camera / IMU (если нужны, можно оставить, но для задания не критичны)
        ],
        remappings=[
            ('/lidar/raw', '/scan'),
            ('/model/robot/tf', '/tf'),
            ('/model/robot/cmd_vel', '/cmd_vel'),
        ],
        output='screen',
        parameters=[{'use_sim_time': True}]
    )

    # 6. Static TF (Костыли из прошлого задания)
    lidar_tf = Node(
        package='tf2_ros',
        executable='static_transform_publisher',
        arguments=['0','0','0','0','0','0', 'lidar_link', 'robot/head/lidar_sensor']
    )
    
    imu_tf = Node(
        package='tf2_ros',
        executable='static_transform_publisher',
        arguments=['0','0','0','0','0','0', 'imu_link', 'robot/base_link/imu_sensor']
    )

    # 7. НАШ АВТОНОМНЫЙ УЗЕЛ
    obstacle_stop_node = Node(
        package='test_robot',
        executable='obstacle_stop', # Имя из setup.py
        name='obstacle_stopper',
        output='screen',
        parameters=[{'use_sim_time': True}]
    )

    return LaunchDescription([
        gz_sim,
        robot_state_publisher,
        bridge,
        lidar_tf,
        imu_tf,
        
        # Сначала спавним робота
        TimerAction(period=3.0, actions=[create]),
        
        # Потом запускаем визуализацию
        TimerAction(period=5.0, actions=[rviz]),
        
        # И в конце запускаем "мозг", чтобы он не начал ехать до того, как робот появится
        TimerAction(period=8.0, actions=[obstacle_stop_node]),
    ])
