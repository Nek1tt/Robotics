from launch import LaunchDescription
from launch_ros.actions import Node
from launch.actions import DeclareLaunchArgument
from launch.substitutions import LaunchConfiguration



def generate_launch_description():
    return LaunchDescription([
        DeclareLaunchArgument(
            'radius',
            default_value='10.0',
            description='Carrot radius'
        ),
        DeclareLaunchArgument(
            'target_frame', 
            default_value='carrot1',
            description='Target frame name.'
        ),
        DeclareLaunchArgument(
            'direction_of_rotation',
            default_value = '1',
            description = 'Direction of rotation. 1 to clockwise, -1 to counterclockwise'
        ),
        Node(
            package='turtlesim',
            executable='turtlesim_node',
            name='sim'
        ),
        Node(
            package='broadcaster_with_carrot',
            executable='turtle1_broadcaster',
            name='broadcaster1',
            parameters=[
                {'turtlename': 'turtle1'}
            ]
        ),
        Node(
            package='broadcaster_with_carrot',
            executable='turtle1_broadcaster',
            name='broadcaster2',
            parameters=[
                {'turtlename': 'turtle2'}
            ]
        ),
        Node(
            package='broadcaster_with_carrot',
            executable='carrot_frame_broadcaster',
            name='carrot_broadcaster',
            parameters=[{'radius': LaunchConfiguration('radius')},
                        {'direction_of_rotation': LaunchConfiguration('direction_of_rotation')}
                        ],
        ),
        Node(
            package='broadcaster_with_carrot',
            executable='turtle1_listener',
            name='listener',
            parameters=[
                {'target_frame': LaunchConfiguration('target_frame')}
            ]
        ),
    ])