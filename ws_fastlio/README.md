# ws_fastlio — FAST-LIO2 SLAM Workspace

## Role
SLAM algorithm workspace. Receives LiDAR point cloud and IMU data,
runs FAST-LIO2 (Ericsii ROS2 fork), and outputs a point cloud map on shutdown.

## Packages
| Package | Description |
|---------|-------------|
| `FAST_LIO_ROS2` | FAST-LIO2 SLAM algorithm (Ericsii fork) |
| `imu_converter` | Custom bridge node — converts IMU unit g → m/s² |

## Subscribed Topics
| Topic | Source |
|-------|--------|
| `/livox/lidar` | livox_ros_driver2 |
| `/livox/imu_converted` | imu_converter (converted from `/livox/imu`) |

## Output
All PCD maps and logs are written to `../fastlio_output/` (not inside this source tree).
See `../fastlio_output/README.md` for details.

## Key Files
- `src/FAST_LIO_ROS2/config/mid360.yaml` — SLAM parameters
- `src/FAST_LIO_ROS2/src/laserMapping.cpp` — pcl_wait_save block must be UNCOMMENTED
- `src/imu_converter/setup.cfg` — required for `ros2 run imu_converter`

## Dependencies
- `ws_livox` must be sourced and running during all mapping sessions

## Cross-Device Note
After moving or cloning to a new device, run `colcon build` inside this directory
to recompile ROOT_DIR path (resolved from $ENV{HOME} at build time).
