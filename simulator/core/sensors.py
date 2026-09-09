import random
import math
import numpy as np


class GPS:
    """GPS sensor simulation with noise and drift"""
    
    def __init__(self, noise_level=0.5, drift_rate=0.01):
        self.noise_level = noise_level
        self.drift_rate = drift_rate
        self.drift_x = 0.0
        self.drift_y = 0.0
        self.drift_z = 0.0
        self.fix_quality = 1.0
        
    def update(self, true_x: float, true_y: float, true_z: float, delta_time: float) -> tuple:
        """Simulate GPS reading with noise and drift"""
        # Update drift (random walk)
        self.drift_x += random.gauss(0, self.drift_rate) * delta_time
        self.drift_y += random.gauss(0, self.drift_rate) * delta_time
        self.drift_z += random.gauss(0, self.drift_rate) * delta_time
        
        # Add noise
        noise_x = random.gauss(0, self.noise_level)
        noise_y = random.gauss(0, self.noise_level)
        noise_z = random.gauss(0, self.noise_level)
        
        # Simulate signal loss
        if random.random() < 0.001:  # 0.1% chance of signal loss
            self.fix_quality = 0
            return (true_x, true_y, true_z)
        
        self.fix_quality = min(1.0, self.fix_quality + 0.01)
        
        return (
            true_x + self.drift_x + noise_x,
            true_y + self.drift_y + noise_y,
            true_z + self.drift_z + noise_z
        )


class IMU:
    """Inertial Measurement Unit simulation"""
    
    def __init__(self):
        self.accel_noise = 0.05  # m/s²
        self.gyro_noise = 0.01  # rad/s
        self.bias_x = 0.0
        self.bias_y = 0.0
        self.bias_z = 0.0
        self.gyro_bias_x = 0.0
        self.gyro_bias_y = 0.0
        self.gyro_bias_z = 0.0
        
    def update(self, true_accel: tuple, true_gyro: tuple) -> dict:
        """Simulate IMU readings with noise and bias"""
        # Add bias drift
        self.bias_x += random.gauss(0, 0.001)
        self.bias_y += random.gauss(0, 0.001)
        self.bias_z += random.gauss(0, 0.001)
        
        # Accelerometer
        accel_x = true_accel[0] + self.bias_x + random.gauss(0, self.accel_noise)
        accel_y = true_accel[1] + self.bias_y + random.gauss(0, self.accel_noise)
        accel_z = true_accel[2] + self.bias_z + random.gauss(0, self.accel_noise)
        
        # Gyroscope
        gyro_x = true_gyro[0] + self.gyro_bias_x + random.gauss(0, self.gyro_noise)
        gyro_y = true_gyro[1] + self.gyro_bias_y + random.gauss(0, self.gyro_noise)
        gyro_z = true_gyro[2] + self.gyro_bias_z + random.gauss(0, self.gyro_noise)
        
        return {
            "acceleration": (accel_x, accel_y, accel_z),
            "gyroscope": (gyro_x, gyro_y, gyro_z)
        }


class Barometer:
    """Barometric pressure sensor for altitude"""
    
    def __init__(self, noise_level=0.3):
        self.noise_level = noise_level
        self.pressure_sea_level = 1013.25  # hPa
        
    def update(self, altitude: float) -> float:
        """Simulate barometric altitude reading"""
        # Add noise
        noise = random.gauss(0, self.noise_level)
        return altitude + noise


class Magnetometer:
    """Magnetic compass sensor"""
    
    def __init__(self, noise_level=0.5):
        self.noise_level = noise_level
        self.declination = 0  # degrees
        
    def update(self, heading: float) -> float:
        """Simulate magnetic heading reading"""
        # Add noise and declination
        noise = random.gauss(0, self.noise_level)
        return (heading + self.declination + noise) % 360