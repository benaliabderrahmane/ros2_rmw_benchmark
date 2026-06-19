cmake_minimum_required(VERSION 3.8)
project(bench_nodes)

if(NOT CMAKE_CXX_STANDARD)
  set(CMAKE_CXX_STANDARD 17)
endif()

find_package(ament_cmake REQUIRED)
find_package(rclcpp REQUIRED)
find_package(std_msgs REQUIRED)
find_package(rosidl_default_generators REQUIRED)

rosidl_generate_interfaces(${PROJECT_NAME}
  "msg/FixedMsg.msg")

add_executable(load_node src/load_node.cpp)
ament_target_dependencies(load_node rclcpp std_msgs)

# Link the node against this package's own generated typesupport (FixedMsg).
rosidl_get_typesupport_target(cpp_typesupport_target ${PROJECT_NAME} rosidl_typesupport_cpp)
target_link_libraries(load_node ${cpp_typesupport_target})

install(TARGETS load_node
  DESTINATION lib/${PROJECT_NAME})

ament_package()
