import struct
import os
import glob
import numpy as np

_pcd_dir = os.path.expanduser("~/Fast_lio2_ROS2/fastlio_output/PCD")
_ply_dir = os.path.expanduser("~/Fast_lio2_ROS2/fastlio_output/PLY")

_pcd_files = sorted(glob.glob(os.path.join(_pcd_dir, "scans_*.pcd")))
if not _pcd_files:
    raise FileNotFoundError(f"No scans_*.pcd files found in {_pcd_dir}")

pcd_path = _pcd_files[-1]
ply_path = os.path.join(_ply_dir, os.path.splitext(os.path.basename(pcd_path))[0] + ".ply")

print("Reading PCD header...")
fields, sizes, types, num_points = [], [], [], 0

with open(pcd_path, 'rb') as f:
    while True:
        line = f.readline().decode('utf-8', errors='ignore').strip()
        if line.startswith('FIELDS'): fields = line.split()[1:]
        elif line.startswith('SIZE'): sizes = list(map(int, line.split()[1:]))
        elif line.startswith('TYPE'): types = line.split()[1:]
        elif line.startswith('POINTS'): num_points = int(line.split()[1])
        elif line.startswith('DATA'):
            break
    binary_data = f.read()

print(f"Fields: {fields}")
print(f"Points: {num_points}")

# Build numpy dtype
dtype_map = {'F': 'f', 'I': 'i', 'U': 'u'}
np_dtype = np.dtype([(f, f'<{dtype_map[t]}{s}') for f, t, s in zip(fields, types, sizes)])
arr = np.frombuffer(binary_data, dtype=np_dtype, count=num_points)

x = arr['x'].astype(np.float32)
y = arr['y'].astype(np.float32)
z = arr['z'].astype(np.float32)
intensity = arr['intensity'].astype(np.float32)

print("Writing binary PLY with intensity...")
header = (
    "ply\n"
    "format binary_little_endian 1.0\n"
    f"element vertex {num_points}\n"
    "property float x\n"
    "property float y\n"
    "property float z\n"
    "property float intensity\n"
    "end_header\n"
)

out = np.zeros(num_points, dtype=[('x','<f4'),('y','<f4'),('z','<f4'),('intensity','<f4')])
out['x'] = x
out['y'] = y
out['z'] = z
out['intensity'] = intensity

with open(ply_path, 'wb') as f:
    f.write(header.encode('utf-8'))
    f.write(out.tobytes())

print(f"Done! Saved to: {ply_path}")
