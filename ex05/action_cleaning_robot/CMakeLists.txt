cmake_minimum_required(VERSION 3.5)
project(action_cleaning_robot)

find_package(ament_cmake REQUIRED)
find_package(rclpy REQUIRED)
find_package(rosidl_default_generators REQUIRED)

rosidl_generate_interfaces(${PROJECT_NAME}
  "action/CleaningTask.action"
)

ament_export_dependencies(rosidl_default_runtime)

install(PROGRAMS
  action_cleaning_robot/cleaning_action_server.py
  DESTINATION lib/${PROJECT_NAME}
  RENAME cleaning_action_server
)

install(PROGRAMS
  action_cleaning_robot/cleaning_action_client.py
  DESTINATION lib/${PROJECT_NAME}
  RENAME cleaning_action_client
)


ament_package()

