cmake_minimum_required(VERSION 3.8)
project(test_robot)

find_package(ament_cmake REQUIRED)

install(PROGRAMS
  square_mover/square_mover.py
  DESTINATION lib/${PROJECT_NAME}
)

install(
  DIRECTORY launch urdf rviz config
  DESTINATION share/${PROJECT_NAME}
)

ament_package()

