# ws_livox — LiDAR ROS2 Driver Workspace

## Role
ROS2 driver workspace for Livox Mid-360 LiDAR.
Bridges raw hardware UDP data into ROS2 topics.

## Published Topics
| Topic | Type | Description |
|-------|------|-------------|
| `/livox/lidar` | `livox_ros_driver2/msg/CustomMsg` | Point cloud (xfer_format = 1) |
| `/livox/imu` | `sensor_msgs/msg/Imu` | Raw IMU data (unit: g) |

## Key Configuration
- `config/MID360_config.json` — LiDAR IP and host IP settings
- `launch_ROS2/msg_MID360_launch.py` — xfer_format = 1 (required for FAST-LIO2)

## ⚠️ Dual Config Trap
`colcon build` copies source config to `install/`. Always edit the **source** config,
then rebuild, then verify the installed copy matches.

## Dependencies
- Livox-SDK2 installed system-wide (see `../Livox-SDK2/`)

## Cross-Device Note
After moving or cloning to a new device, run `colcon build --cmake-args -DDISTRO_ROS=jazzy`
inside this directory to refresh all install paths before launching.
