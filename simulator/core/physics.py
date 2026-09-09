import math


class PhysicsEngine:
    """Realistic flight dynamics with thrust, gravity, drag, and inertia"""
    
    def __init__(self):
        # Physical constants
        self.gravity = 9.81  # m/s²
        self.air_density = 1.225  # kg/m³ at sea level
        
        # Drone parameters
        self.mass = 1.5  # kg
        self.thrust_max = 25.0  # N
        self.drag_coefficient = 0.3
        self.cross_section_area = 0.1  # m²
        
        # Flight dynamics
        self.thrust = 0.0
        self.drag_force = 0.0
        self.lift_force = 0.0
        self.weight = self.mass * self.gravity
        
        # Angular dynamics (roll, pitch, yaw)
        self.roll_rate = 0.0
        self.pitch_rate = 0.0
        self.yaw_rate = 0.0
        self.roll_angle = 0.0
        self.pitch_angle = 0.0
        self.yaw_angle = 0.0
        
        # Inertia (simplified)
        self.inertia_xx = 0.01  # kg·m²
        self.inertia_yy = 0.01
        self.inertia_zz = 0.02
        
    def calculate_thrust(self, throttle: float, altitude: float) -> float:
        """Calculate thrust based on throttle and altitude"""
        # Thrust decreases with altitude
        altitude_factor = math.exp(-altitude / 1000)  # 1000m scale height
        thrust = self.thrust_max * throttle * altitude_factor
        return max(0, thrust)
    
    def calculate_drag(self, velocity_x: float, velocity_y: float, velocity_z: float) -> tuple:
        """Calculate drag forces in all axes"""
        velocity_magnitude = math.sqrt(velocity_x**2 + velocity_y**2 + velocity_z**2)
        
        if velocity_magnitude < 0.01:
            return (0, 0, 0)
        
        # Drag force: F_drag = 0.5 * rho * v² * Cd * A
        drag_magnitude = 0.5 * self.air_density * velocity_magnitude**2 * self.drag_coefficient * self.cross_section_area
        
        # Direction opposes velocity
        dx = -velocity_x / velocity_magnitude * drag_magnitude
        dy = -velocity_y / velocity_magnitude * drag_magnitude
        dz = -velocity_z / velocity_magnitude * drag_magnitude
        
        return (dx, dy, dz)
    
    def calculate_lift(self, velocity_x: float, velocity_y: float, velocity_z: float) -> float:
        """Calculate aerodynamic lift"""
        horizontal_speed = math.sqrt(velocity_x**2 + velocity_y**2)
        # Simple lift model
        lift = 0.5 * self.air_density * horizontal_speed**2 * 0.5
        return max(0, lift)
    
    def update_dynamics(self, 
                        velocity_x: float, velocity_y: float, velocity_z: float,
                        throttle: float, 
                        altitude: float,
                        target_pitch: float, target_roll: float, target_yaw: float,
                        delta_time: float) -> tuple:
        """Update flight dynamics and return new accelerations"""
        
        # Calculate thrust
        self.thrust = self.calculate_thrust(throttle, altitude)
        
        # Calculate drag
        drag_x, drag_y, drag_z = self.calculate_drag(velocity_x, velocity_y, velocity_z)
        
        # Calculate lift
        self.lift_force = self.calculate_lift(velocity_x, velocity_y, velocity_z)
        
        # Weight force (always downward)
        weight_z = -self.weight
        
        # Acceleration from thrust (assuming thrust is upward)
        # Convert thrust to acceleration: a = F / m
        thrust_accel_z = self.thrust / self.mass
        
        # Total acceleration
        accel_x = drag_x / self.mass
        accel_y = drag_y / self.mass
        accel_z = (thrust_accel_z + weight_z / self.mass + self.lift_force / self.mass + drag_z / self.mass)
        
        # Angular dynamics (simplified PID-like control)
        pitch_rate = (target_pitch - self.pitch_angle) * 2.0
        roll_rate = (target_roll - self.roll_angle) * 2.0
        yaw_rate = (target_yaw - self.yaw_angle) * 1.0
        
        # Update angles
        self.pitch_angle += pitch_rate * delta_time
        self.roll_angle += roll_rate * delta_time
        self.yaw_angle += yaw_rate * delta_time
        
        # Clamp angles
        self.pitch_angle = max(-45, min(45, self.pitch_angle))
        self.roll_angle = max(-45, min(45, self.roll_angle))
        self.yaw_angle = self.yaw_angle % 360
        
        return (accel_x, accel_y, accel_z)