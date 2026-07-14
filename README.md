# Mid360-Fast_lio2_ROS2

FAST-LIO2 SLAM on ROS2 for the Livox Mid-360 LiDAR — live mapping, ros2-bag replay, and PCD/PLY map export.

Tested on: **Ubuntu 24.04 / ROS2 Jazzy / GCC 13.3.0**
Also verified on: **Ubuntu 22.04 / ROS2 Humble** (see notes below)

---

## 1. Clone

Always use `--recurse-submodules` — otherwise Livox-SDK2, FAST_LIO_ROS2, and livox_ros_driver2 will be empty:

```bash
git clone --recurse-submodules https://github.com/Doctorcro/Mid360-Fast_lio2_ROS2.git
cd Mid360-Fast_lio2_ROS2
```

If you already cloned without it, recover with:
```bash
git submodule update --init --recursive
```

---

## 2. Per-Device Configuration

Before building, update these two files for your network:

**`ws_livox/src/livox_ros_driver2/config/MID360_config.json`**
```json
"host_net_info": {
  "cmd_data_ip":   "<YOUR_HOST_IP>",   // e.g. 192.168.1.50
  "push_msg_ip":   "<YOUR_HOST_IP>",
  "point_data_ip": "<YOUR_HOST_IP>",
  "imu_data_ip":   "<YOUR_HOST_IP>"
},
"lidar_configs": [
  { "ip": "<YOUR_LIDAR_IP>" }           // e.g. 192.168.1.3
]
```

A template is at `config/MID360_config.template.json`.

**Your host's network interface must also be preconfigured** with a static IP in the same subnet as the LiDAR (e.g. `192.168.1.50/24`) *before* launching anything — the driver does not set this for you:
```bash
sudo ip addr add 192.168.1.50/24 dev <YOUR_ETH_INTERFACE>
```
Verify the LiDAR is reachable: `ping <YOUR_LIDAR_IP>`.

---

## 3. Build Livox-SDK2

Must be built and installed before any ROS2 packages:

```bash
cd Livox-SDK2
mkdir -p build && cd build
cmake .. && make -j$(nproc)
sudo make install
sudo ldconfig
cd ../..
```

---

## 4. Build ws_livox (livox_ros_driver2)

**Do not use plain `colcon build` here** — the package requires its own `build.sh` to set the ROS distro correctly.

For **Jazzy**:
```bash
cd ws_livox/src/livox_ros_driver2
./build.sh jazzy
cd ../../..
```

For **Humble**:
```bash
cd ws_livox/src/livox_ros_driver2
./build.sh humble
cd ../../..
```

---

## 5. Install System Dependencies

```bash
# For Jazzy
sudo apt install -y ros-jazzy-pcl-ros

# For Humble
sudo apt install -y ros-humble-pcl-ros
```

---

## 6. Build ws_fastlio (FAST-LIO2 + imu_converter)

Source ws_livox first so CMake can find `livox_ros_driver2Config.cmake`:

```bash
source ws_livox/install/setup.bash
cd ws_fastlio
colcon build --symlink-install
cd ..
```

If `ikd-Tree` headers are missing, the submodule inside FAST_LIO_ROS2 wasn't checked out:
```bash
git -C ws_fastlio/src/FAST_LIO_ROS2 submodule update --init --recursive
# then rebuild
```

---

## 7. Run (Mapping/replay bag)
#### For jazzy

```bash
# bash cammand should be input in every terminal
source /opt/ros/jazzy/setup.bash
source Mid360-Fast_lio2_ROS2/ws_livox/install/setup.bash
source Mid360-Fast_lio2_ROS2/ws_fastlio/install/setup.bash

# for mapping 
# terminal --1  Launching the SDK & livox-ros2-driver
# Make sure the lidar is pluged to the computer and lidar IP is setup
# Wait until you see "Init lds lidar success!" then you are good to go.
ros2 launch livox_ros_driver2 msg_MID360_launch.py

# terminal --2  Launch Fastlio2
ros2 launch fast_lio mapping.launch.py config_file:=mid360.yaml

# terminal --3  Recoed ros2-bag
ros2 bag record -o ~/<target_directory>/map$(date +%Y%m%d_%H%M%S) /livox/lidar /livox/imu /livox/imu_converted /path



# for ros2-bag replay
# terminal --1  Launching the Fastlio2
ros2 launch fast_lio mapping.launch.py config_file:=mid360.yaml use_sim_time:=true

# terminal --2  replay the ros2-bag
ros2 launch fast_lio mapping.launch.py --config_file:=mid360.yaml --use_sim_time:=true
# use_sim_time:= >> to prevent clock mismatches while in replay (prevent nod time mismatch)
```


#### For humble

```bash
# bash cammand should be input in every terminal
source /opt/ros/humble/setup.bash
source Mid360-Fast_lio2_ROS2/ws_livox/install/setup.bash
source Mid360-Fast_lio2_ROS2/ws_fastlio/install/setup.bash

# for mapping 
# terminal --1  Launching the SDK & livox-ros2-driver
# Make sure the lidar is pluged to the computer and lidar IP is setup
# Wait until you see "Init lds lidar success!" then you are good to go.
ros2 launch livox_ros_driver2 msg_MID360_launch.py

# terminal --2  Launch Fastlio2
ros2 launch fast_lio mapping.launch.py config_file:=mid360.yaml

# terminal --3  Recoed ros2-bag
ros2 bag record -o ~/<target_directory>/map$(date +%Y%m%d_%H%M%S) /livox/lidar /livox/imu /livox/imu_converted /path



# for ros2-bag replay
# terminal --1  Launching the Fastlio2
ros2 launch fast_lio mapping.launch.py config_file:=mid360.yaml use_sim_time:=true

# terminal --2  replay the ros2-bag
ros2 launch fast_lio mapping.launch.py --config_file:=mid360.yaml --use_sim_time:=true
# use_sim_time:= >> to prevent clock mismatches while in replay (prevent nod time mismatch)
```

---

## 8. Re-calibrate Gravity Alignment (after remounting the LiDAR)

The gravity TF quaternion in `launch/mapping.launch.py` is specific to how the sensor is physically mounted. If you remount or reorient the LiDAR, redo this:

1. Run mapping and record a ros2-bag for **at least 30 seconds** while the sensor sits still in its new mount:
   ```bash
	 ros2 bag record -o <bag_name> /livox/imu_converted
   ```
3. Extract the gravity vector (Gravity TF quaternion) from the bag:
   ```bash
	 python3 Mid360-Fast_lio2_ROS2/scripts/gravity_align.py \
	  <target_ros-bag_path> \
	  --storage sqlite3
   ```
4. After you run the script, you will see a output message  -- 
	 eg: ros2 run tf2_ros static_transform_publisher **0 0 0 -0.70710529 -0.00120913 0.00000000 0.70710724** --frame-id world_aligned --child-frame-id camera_init
	 the number represents the: 
	 `'--x', '0', '--y', '0', '--z', '0',`
	 `'--qx', '-0.70710529', '--qy', '-0.00120913',`
	 `'--qz', '0.00000000', '--qw', '0.70710724',`
5. Take the printed `--qx --qy --qz --qw` values and paste them into the `gravity_tf_node` arguments in `ws_fastlio/src/FAST_LIO_ROS2/launch/mapping.launch.py` (around the `--qx/--qy/--qz/--qw` line).
```
 **You can find the parmeter below:**
 
 gravity_tf_node = Node(
        package='tf2_ros',
        executable='static_transform_publisher',
        arguments=[
            '--x', '0', '--y', '0', '--z', '0',
            '--qx', '-0.70710529', '--qy', '-0.00120913',
            '--qz', '0.00000000', '--qw', '0.70710724',
            '--frame-id', 'world_aligned',
            '--child-frame-id', 'camera_init'
```

6. Rebuild `ws_fastlio` so the launch file change takes effect:
   ```bash
   cd ws_fastlio && colcon build --symlink-install && cd ..
   ```
   

---

## Notes

- **Gravity TF quaternion** in `launch/mapping.launch.py` is calibrated for this specific sensor mount. See step 8 above if the sensor is remounted.
- **PCD output** goes to `<repo_root>/fastlio_output/PCD/` (resolved automatically from the CMakeLists.txt location, independent of what you named the clone directory). Convert to PLY with `scripts/convert_with_intensity.py`.
- `scripts/convert_with_intensity.py` currently hardcodes `~/Fast_lio2_ROS2/fastlio_output/{PCD,PLY}` at the top of the file. If you cloned this repo under a different directory name (e.g. `Mid360-Fast_lio2_ROS2`), edit those two paths in the script to match your actual clone path before running it.
- `pcd_save_en` is set to `false` in `config/mid360.yaml` by default — set to `true` to save maps.
- **Testing ros2-bag** https://drive.google.com/drive/u/1/folders/1-wiL6GzRh8jNeGojVtZaCDNvxl62ghWh  --dowload the whole folder.

