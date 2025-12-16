cmake_minimum_required(VERSION 3.8)
project(test_robot)

find_package(ament_cmake REQUIRED)
find_package(ament_cmake_python REQUIRED)
find_package(rclpy REQUIRED)

ament_python_install_package(${PROJECT_NAME})

install(PROGRAMS
  test_robot/depth_stop.py
  DESTINATION lib/${PROJECT_NAME}
  RENAME depth_stop
)

install(DIRECTORY launch urdf rviz
  DESTINATION share/${PROJECT_NAME}
)

ament_package()
