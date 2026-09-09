class PID:
    """PID Controller for autonomous flight control"""
    
    def __init__(self, kp: float, ki: float, kd: float, 
                 setpoint: float = 0.0, output_limits: tuple = None):
        self.kp = kp
        self.ki = ki
        self.kd = kd
        self.setpoint = setpoint
        self.integral = 0.0
        self.previous_error = 0.0
        self.output_limits = output_limits
        self.last_time = 0
        
    def update(self, measurement: float, delta_time: float) -> float:
        """Calculate PID output"""
        error = self.setpoint - measurement
        
        # Proportional term
        p_term = self.kp * error
        
        # Integral term
        self.integral += error * delta_time
        i_term = self.ki * self.integral
        
        # Derivative term
        derivative = (error - self.previous_error) / delta_time if delta_time > 0 else 0
        d_term = self.kd * derivative
        
        # Calculate output
        output = p_term + i_term + d_term
        
        # Apply limits
        if self.output_limits:
            output = max(self.output_limits[0], min(self.output_limits[1], output))
            
        self.previous_error = error
        
        return output
    
    def reset(self):
        """Reset PID controller state"""
        self.integral = 0.0
        self.previous_error = 0.0


class AltitudeController:
    """Altitude hold controller using PID"""
    
    def __init__(self, drone, max_climb=5.0, max_descend=-5.0):
        self.drone = drone
        self.pid = PID(kp=1.5, ki=0.3, kd=0.1, output_limits=(max_descend, max_climb))
        self.target_altitude = 0.0
        
    def update(self, target_altitude: float, delta_time: float) -> float:
        """Update altitude control and return climb rate command"""
        self.target_altitude = target_altitude
        self.pid.setpoint = target_altitude
        return self.pid.update(self.drone.z, delta_time)


class VelocityController:
    """Velocity hold controller"""
    
    def __init__(self, drone, max_accel=2.0):
        self.drone = drone
        self.pid_x = PID(kp=1.0, ki=0.1, kd=0.05, output_limits=(-max_accel, max_accel))
        self.pid_y = PID(kp=1.0, ki=0.1, kd=0.05, output_limits=(-max_accel, max_accel))
        self.target_velocity_x = 0.0
        self.target_velocity_y = 0.0
        
    def update(self, target_vx: float, target_vy: float, delta_time: float) -> tuple:
        """Update velocity control and return acceleration commands"""
        self.target_velocity_x = target_vx
        self.target_velocity_y = target_vy
        
        self.pid_x.setpoint = target_vx
        self.pid_y.setpoint = target_vy
        
        accel_x = self.pid_x.update(self.drone.velocity_x, delta_time)
        accel_y = self.pid_y.update(self.drone.velocity_y, delta_time)
        
        return (accel_x, accel_y)