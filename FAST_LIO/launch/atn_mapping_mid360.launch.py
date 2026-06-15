import os.path

from ament_index_python.packages import get_package_share_directory

from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch.substitutions import LaunchConfiguration
from launch.conditions import IfCondition

from launch_ros.actions import Node, SetUseSimTime


def generate_launch_description():
    package_path = get_package_share_directory('fast_lio')

    # Create LaunchConfigurations for the parameters with default values (not in config file)
    feature_extract_enable_param = LaunchConfiguration('feature_extract_enable', default='false') # bool
    point_filter_num_param = LaunchConfiguration('point_filter_num', default='3')                 # int
    max_iteration_param = LaunchConfiguration('max_iteration', default='3')                       # int
    filter_size_surf_param = LaunchConfiguration('filter_size_surf', default='0.5')               # double
    filter_size_map_param = LaunchConfiguration('filter_size_map', default='0.5')                 # double
    cube_side_length_param = LaunchConfiguration('cube_side_length', default='1000.0')            # double
    runtime_pos_log_enable_param = LaunchConfiguration('runtime_pos_log_enable', default='false')  # bool
    blind_distance = LaunchConfiguration('preprocess.blind', default='0.9')  # double

    default_config_path = os.path.join(package_path, 'config', 'mid360.yaml')
    default_rviz_config_path = os.path.join(
        package_path, 'rviz_cfg', 'fastlio.rviz')


    use_sim_time = LaunchConfiguration('use_sim_time')
    config_path = LaunchConfiguration('config_path')
    rviz_use = LaunchConfiguration('rviz')
    rviz_cfg = LaunchConfiguration('rviz_cfg')

    declare_use_sim_time_cmd = DeclareLaunchArgument(
        'use_sim_time', default_value='false',
        description='Use simulation (Gazebo) clock if true'
    )
    declare_config_path_cmd = DeclareLaunchArgument(
        'config_path', default_value=default_config_path,
        description='Yaml config file path'
    )
    declare_rviz_cmd = DeclareLaunchArgument(
        'rviz', default_value='true',
        description='Use RViz to monitor results'
    )
    declare_rviz_config_path_cmd = DeclareLaunchArgument(
        'rviz_cfg', default_value=default_rviz_config_path,
        description='RViz config file path'
    )

    fast_lio_node = Node(
        package='fast_lio',
        executable='fastlio_mapping',
        parameters=[config_path,
                    {'use_sim_time': use_sim_time,
                    'feature_extract_enable': feature_extract_enable_param,
                    'point_filter_num': point_filter_num_param,
                    'max_iteration': max_iteration_param,
                    'filter_size_surf': filter_size_surf_param,
                    'filter_size_map': filter_size_map_param,
                    'cube_side_length': cube_side_length_param,
                    'runtime_pos_log_enable': runtime_pos_log_enable_param,
                    'preprocess.blind': blind_distance}],
        output='screen'
    )
    # rviz_node = Node(
    #     package='rviz2',
    #     executable='rviz2',
    #     arguments=['-d', rviz_cfg],
    #     condition=IfCondition(rviz_use)
    # )

    ld = LaunchDescription()
    ld.add_action(declare_use_sim_time_cmd)
    ld.add_action(declare_config_path_cmd)
    ld.add_action(declare_rviz_cmd)
    ld.add_action(declare_rviz_config_path_cmd)

    # All TFs specific to the MID360 upside-down mount on the Hummel drone.
    # FAST-LIO world frame 'camera_init' is NED-like (initialized from upside-down IMU).
    # FAST-LIO body frame 'body' is FRD (IMU axes, also upside-down).
    #
    # odom (ENU) -> camera_init: 180 deg roll, qx=1 qy=0 qz=0 qw=0
    tf_odom_to_camera_init = Node(
        package='tf2_ros',
        executable='static_transform_publisher',
        name='tf_odom_to_camera_init',
        arguments=['0', '0', '0', '1', '0', '0', '0', 'odom', 'camera_init'],
    )

    # body (FRD) -> base_link (FLU): 180 deg roll, qx=1 qy=0 qz=0 qw=0
    tf_body_to_base_link = Node(
        package='tf2_ros',
        executable='static_transform_publisher',
        name='tf_body_to_base_link',
        arguments=['0', '0', '0', '1', '0', '0', '0', 'body', 'base_link'],
    )

    # body (FRD) -> fmu/base_link (FRD): identity
    tf_body_to_fmu = Node(
        package='tf2_ros',
        executable='static_transform_publisher',
        name='tf_body_to_fmu_base_link',
        arguments=['0', '0', '0', '0', '0', '0', '1', 'body', 'fmu/base_link'],
    )

    ld.add_action(fast_lio_node)
    ld.add_action(tf_odom_to_camera_init)
    ld.add_action(tf_body_to_base_link)
    ld.add_action(tf_body_to_fmu)
    # ld.add_action(rviz_node)

    return ld
