from setuptools import setup
setup(
    name='imu_converter',
    version='0.0.1',
    packages=['imu_converter'],
    install_requires=['setuptools'],
    entry_points={
        'console_scripts': [
            'imu_converter_node = imu_converter.imu_converter_node:main',
        ],
    },
)
