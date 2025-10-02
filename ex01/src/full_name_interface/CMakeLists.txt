cmake_minimum_required(VERSION 3.5)
project(full_name_interface)

find_package(ament_cmake REQUIRED)
find_package(rosidl_default_generators REQUIRED)

rosidl_generate_interfaces(${PROJECT_NAME}
  "srv/FullNameSumService.srv"
)

ament_package()

