#!/usr/bin/env python3
"""
Extract gravity vector from rosbag IMU data and compute
the static TF quaternion for gravity alignment.

Usage:
    python3 gravity_align.py <BAG_PATH> [--imu-topic /livox/imu_converted] [--samples 200]

Output:
    - Measured gravity vector in IMU frame
    - Rotation angle and axis
    - Quaternion [qx, qy, qz, qw]
    - Ready-to-use static_transform_publisher command
"""

import argparse
import sys
import numpy as np

def extract_gravity(bag_path, imu_topic, num_samples, storage_id):
    """Read first N IMU messages and return averaged acceleration vector."""
    from rosbag2_py import SequentialReader, StorageOptions, ConverterOptions
    from rclpy.serialization import deserialize_message
    from sensor_msgs.msg import Imu

    reader = SequentialReader()
    storage_options = StorageOptions(uri=bag_path, storage_id=storage_id)
    converter_options = ConverterOptions(
        input_serialization_format='cdr',
        output_serialization_format='cdr'
    )
    reader.open(storage_options, converter_options)

    # Filter to IMU topic only
    from rosbag2_py import StorageFilter
    reader.set_filter(StorageFilter(topics=[imu_topic]))

    accel_samples = []
    while reader.has_next() and len(accel_samples) < num_samples:
        topic, data, timestamp = reader.read_next()
        msg = deserialize_message(data, Imu)
        accel_samples.append([
            msg.linear_acceleration.x,
            msg.linear_acceleration.y,
            msg.linear_acceleration.z
        ])

    if len(accel_samples) == 0:
        print(f"ERROR: No IMU messages found on topic '{imu_topic}'")
        print("Check: is the topic name correct? Was ws_livox sourced?")
        sys.exit(1)

    print(f"Read {len(accel_samples)} IMU samples from '{imu_topic}'")
    gravity = np.mean(accel_samples, axis=0)
    gravity_std = np.std(accel_samples, axis=0)
    print(f"Mean acceleration (IMU frame): [{gravity[0]:.6f}, {gravity[1]:.6f}, {gravity[2]:.6f}]")
    print(f"Std deviation:                 [{gravity_std[0]:.6f}, {gravity_std[1]:.6f}, {gravity_std[2]:.6f}]")
    print(f"Magnitude: {np.linalg.norm(gravity):.4f} m/s² (expect ~9.81)")

    # Sanity check: magnitude should be close to 9.81 m/s²
    mag = np.linalg.norm(gravity)
    if mag < 8.0 or mag > 12.0:
        print(f"WARNING: gravity magnitude {mag:.2f} is outside expected range [8.0, 12.0]")
        print("This may indicate the bag was NOT recorded with imu_converter (g→m/s²)")
        print("If topic is /livox/imu (raw), magnitude ~1.0 is expected — direction is still valid")

    return gravity


def compute_alignment_quaternion(gravity_imu):
    """
    Compute quaternion that rotates camera_init frame so gravity aligns with -Z.

    The transform is: world_aligned = R * camera_init
    Published as: world_aligned (parent) → camera_init (child)

    gravity_imu: [gx, gy, gz] measured gravity vector in IMU frame
    Returns: [qx, qy, qz, qw]
    """
    g = np.array(gravity_imu, dtype=np.float64)
    g_unit = g / np.linalg.norm(g)

    # The accelerometer reads specific force (reaction to gravity) = upward direction in IMU frame.
    # Map that "up" reading to +Z_world so that the physical down (+Y_cam) maps to -Z_world.
    target = np.array([0.0, 0.0, 1.0])

    # Rotation axis = cross(g_unit, target)
    axis = np.cross(g_unit, target)
    axis_len = np.linalg.norm(axis)

    if axis_len < 1e-8:
        # g is already along Z (aligned or anti-aligned)
        dot = np.dot(g_unit, target)
        if dot > 0:
            print("Gravity already aligned with -Z — no rotation needed")
            return [0.0, 0.0, 0.0, 1.0]
        else:
            print("Gravity anti-aligned (pointing +Z) — 180° rotation around X")
            return [1.0, 0.0, 0.0, 0.0]

    axis = axis / axis_len
    angle = np.arccos(np.clip(np.dot(g_unit, target), -1.0, 1.0))

    # Quaternion from axis-angle: q = [axis * sin(θ/2), cos(θ/2)]
    half = angle / 2.0
    qx = axis[0] * np.sin(half)
    qy = axis[1] * np.sin(half)
    qz = axis[2] * np.sin(half)
    qw = np.cos(half)

    print(f"\nRotation axis:  [{axis[0]:.6f}, {axis[1]:.6f}, {axis[2]:.6f}]")
    print(f"Rotation angle: {np.degrees(angle):.2f}°")
    print(f"Quaternion:     [{qx:.8f}, {qy:.8f}, {qz:.8f}, {qw:.8f}]")

    # Verification: R * g should give [0, 0, -|g|]
    # Using Rodrigues' formula
    K = np.array([
        [0, -axis[2], axis[1]],
        [axis[2], 0, -axis[0]],
        [-axis[1], axis[0], 0]
    ])
    R = np.eye(3) + np.sin(angle) * K + (1 - np.cos(angle)) * (K @ K)
    rotated_g = R @ g_unit
    print(f"\nVerification: R * g_unit = [{rotated_g[0]:.6f}, {rotated_g[1]:.6f}, {rotated_g[2]:.6f}]")
    print(f"Expected:                  [0.000000, 0.000000,  1.000000]")
    error = np.linalg.norm(rotated_g - target)
    if error > 0.01:
        print(f"WARNING: verification error {error:.6f} > 0.01 — quaternion may be wrong")

    return [qx, qy, qz, qw]


def main():
    parser = argparse.ArgumentParser(description='Compute gravity alignment TF from rosbag IMU data')
    parser.add_argument('bag_path', help='Path to the rosbag directory')
    parser.add_argument('--imu-topic', default='/livox/imu_converted',
                        help='IMU topic name (default: /livox/imu_converted)')
    parser.add_argument('--samples', type=int, default=200,
                        help='Number of IMU samples to average (default: 200)')
    parser.add_argument('--storage', default='mcap',
                        help='Bag storage format: mcap or sqlite3 (default: mcap)')
    parser.add_argument('--parent-frame', default='world_aligned',
                        help='Parent frame name (default: world_aligned)')
    parser.add_argument('--child-frame', default='camera_init',
                        help='Child frame name (default: camera_init)')
    args = parser.parse_args()

    print("=" * 60)
    print("GRAVITY ALIGNMENT — TF COMPUTATION")
    print("=" * 60)
    print(f"Bag:       {args.bag_path}")
    print(f"IMU topic: {args.imu_topic}")
    print(f"Samples:   {args.samples}")
    print(f"Storage:   {args.storage}")
    print()

    # Step 1: Extract gravity
    gravity = extract_gravity(args.bag_path, args.imu_topic, args.samples, args.storage)

    # Step 2: Compute quaternion
    print()
    qx, qy, qz, qw = compute_alignment_quaternion(gravity)

    # Step 3: Output the command
    print()
    print("=" * 60)
    print("READY-TO-USE COMMAND")
    print("=" * 60)
    cmd = (
        f"ros2 run tf2_ros static_transform_publisher "
        f"0 0 0 "
        f"{qx:.8f} {qy:.8f} {qz:.8f} {qw:.8f} "
        f"--frame-id {args.parent_frame} "
        f"--child-frame-id {args.child_frame}"
    )
    print(cmd)
    print()
    print("Copy the command above and run it in a dedicated terminal.")
    print(f"Then set RViz2 Fixed Frame to '{args.parent_frame}'.")
    print()

    # Also output as rotation matrix for PLY post-processing
    angle = 2.0 * np.arccos(np.clip(qw, -1.0, 1.0))
    if angle > 1e-8:
        axis = np.array([qx, qy, qz]) / np.sin(angle / 2.0)
    else:
        axis = np.array([1.0, 0.0, 0.0])
    K = np.array([
        [0, -axis[2], axis[1]],
        [axis[2], 0, -axis[0]],
        [-axis[1], axis[0], 0]
    ])
    R = np.eye(3) + np.sin(angle) * K + (1 - np.cos(angle)) * (K @ K)
    print("Rotation matrix (for PLY post-processing):")
    print(f"  [{R[0,0]:.8f}, {R[0,1]:.8f}, {R[0,2]:.8f}]")
    print(f"  [{R[1,0]:.8f}, {R[1,1]:.8f}, {R[1,2]:.8f}]")
    print(f"  [{R[2,0]:.8f}, {R[2,1]:.8f}, {R[2,2]:.8f}]")


if __name__ == '__main__':
    main()
