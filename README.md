# Setup Guide — Mid360 FAST-LIO2 ROS2

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

## 7. Run

```bash
source ws_livox/install/setup.bash
source ws_fastlio/install/setup.bash

# for mapping
ros2 launch fast_lio mapping.launch.py

# for ros2-bag replay
ros2 launch fast_lio mapping.launch.py --config_file:=mid360.yaml --use_sim_time:=true
# use_sim_time:= >> to prevent clock mismatches while in replay (prevent nod time mismatch)
```

For bag replay:
```bash
ros2 bag play <YOUR_BAG_PATH> --clock --rate=1.0 
# "clock" for line-up to sim time
# suggested maximum rate=2.5 for GUP under gtx-1050
```

---

## Notes

- **Gravity TF quaternion** in `launch/mapping.launch.py` is calibrated for this specific sensor mount. Re-run `scripts/gravity_align.py` on a new bag if the sensor is remounted.
- **PCD output** goes to `~/Fast_lio2_ROS2/fastlio_output/PCD/`. Convert to PLY with `scripts/convert_with_intensity.py`.
- `pcd_save_en` is set to `false` in `config/mid360.yaml` by default — set to `true` to save maps.
- **Testing ros2-bag** https://drive.google.com/drive/u/1/folders/1-wiL6GzRh8jNeGojVtZaCDNvxl62ghWh  --dowload the whole folder.
