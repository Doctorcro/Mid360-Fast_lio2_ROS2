import rclpy
from rclpy.node import Node
from sensor_msgs.msg import Imu

class ImuConverter(Node):
    def __init__(self):
        super().__init__('imu_converter')
        # Mid-360 publishes acceleration in [g], FAST-LIO2 requires [m/s²]
        # Conversion factor: 1g = 9.81 m/s²
        self.sub = self.create_subscription(Imu, '/livox/imu', self.callback, 10)
        self.pub = self.create_publisher(Imu, '/livox/imu_converted', 10)

    def callback(self, msg):
        msg.linear_acceleration.x *= 9.81
        msg.linear_acceleration.y *= 9.81
        msg.linear_acceleration.z *= 9.81
        self.pub.publish(msg)

def main():
    rclpy.init()
    node = ImuConverter()
    rclpy.spin(node)

if __name__ == '__main__':
    main()
