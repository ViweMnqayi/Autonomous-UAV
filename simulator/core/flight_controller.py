import math
from simulator.core.pid import PID, AltitudeController, VelocityController


class FlightController:
    def __init__(self, drone):
        self.drone = drone

        # =====================================================
        # FLIGHT TARGETS
        # =====================================================
        self.target_altitude = 0.0
        self.target_speed = 5.0
        self.speed_step = 1.0

        # =====================================================
        # TARGET HORIZONTAL VELOCITY
        # =====================================================
        self.target_velocity_x = 0.0
        self.target_velocity_y = 0.0

        # =====================================================
        # NAVIGATION
        # =====================================================
        self.navigation_mode = "MANUAL"  # MANUAL, HOLD, LANDING, RETURN_HOME, MISSION, GEOFENCE_RECOVERY, AUTONOMOUS
        self.target_x = None
        self.target_y = None

        # =====================================================
        # VERTICAL FLIGHT PHYSICS
        # =====================================================
        self.max_vertical_speed = 5.0
        self.vertical_acceleration = 2.5
        self.vertical_deceleration = 3.0
        self.landing_speed = 2.5
        self.altitude_threshold = 0.5

        # =====================================================
        # HORIZONTAL FLIGHT PHYSICS
        # =====================================================
        self.horizontal_acceleration = 2.0
        self.horizontal_deceleration = 3.0

        # =====================================================
        # RETURN HOME
        # =====================================================
        self.arrival_threshold = 0.5

        # =====================================================
        # PID CONTROLLERS (NEW)
        # =====================================================
        self.use_pid = True  # Toggle between PID and traditional control
        self.altitude_pid = PID(kp=1.5, ki=0.3, kd=0.1, output_limits=(-5.0, 5.0))
        self.velocity_pid_x = PID(kp=1.0, ki=0.1, kd=0.05, output_limits=(-2.0, 2.0))
        self.velocity_pid_y = PID(kp=1.0, ki=0.1, kd=0.05, output_limits=(-2.0, 2.0))
        
        # =====================================================
        # AUTONOMOUS MODE SETTINGS (NEW)
        # =====================================================
        self.autonomous_mode = False
        self.auto_altitude_hold = True
        self.auto_heading_hold = False
        self.target_heading = 0.0
        
        # =====================================================
        # PATH PLANNING (NEW)
        # =====================================================
        self.path_waypoints = []
        self.current_path_index = 0
        self.path_following = False
        
        # =====================================================
        # OBSTACLE AVOIDANCE (NEW)
        # =====================================================
        self.obstacle_avoidance_enabled = True
        self.avoidance_distance = 5.0
        self.avoidance_angle = 45.0

    # =========================================================
    # ALTITUDE
    # =========================================================
    def set_altitude(self, altitude):
        altitude = max(0.0, altitude)
        altitude = min(altitude, self.drone.max_altitude)
        self.target_altitude = altitude
        
        # Update PID setpoint if using PID
        if self.use_pid:
            self.altitude_pid.setpoint = altitude

    # =========================================================
    # SPEED
    # =========================================================
    def set_speed(self, speed):
        speed = max(0.0, speed)
        speed = min(speed, self.drone.max_speed)
        self.target_speed = speed

        # Preserve current movement direction
        current_x = self.target_velocity_x
        current_y = self.target_velocity_y
        magnitude = math.sqrt(current_x ** 2 + current_y ** 2)

        if magnitude > 0:
            self.target_velocity_x = (current_x / magnitude) * self.target_speed
            self.target_velocity_y = (current_y / magnitude) * self.target_speed

    # =========================================================
    # INCREASE/DECREASE SPEED
    # =========================================================
    def increase_speed(self):
        new_speed = self.target_speed + self.speed_step
        if new_speed > self.drone.max_speed:
            new_speed = self.drone.max_speed
        self.set_speed(new_speed)

    def decrease_speed(self):
        new_speed = self.target_speed - self.speed_step
        if new_speed < 0.0:
            new_speed = 0.0
        self.set_speed(new_speed)

    # =========================================================
    # MOVEMENT
    # =========================================================
    def move_forward(self):
        if self.drone.state not in ["FLYING", "TAKING_OFF"]:
            return
        self.navigation_mode = "MANUAL"
        self.target_velocity_x = self.target_speed
        self.target_velocity_y = 0.0

    def move_backward(self):
        if self.drone.state not in ["FLYING", "TAKING_OFF"]:
            return
        self.navigation_mode = "MANUAL"
        self.target_velocity_x = -self.target_speed
        self.target_velocity_y = 0.0

    def move_right(self):
        if self.drone.state not in ["FLYING", "TAKING_OFF"]:
            return
        self.navigation_mode = "MANUAL"
        self.target_velocity_x = 0.0
        self.target_velocity_y = self.target_speed

    def move_left(self):
        if self.drone.state not in ["FLYING", "TAKING_OFF"]:
            return
        self.navigation_mode = "MANUAL"
        self.target_velocity_x = 0.0
        self.target_velocity_y = -self.target_speed

    # =========================================================
    # NAVIGATE TO POSITION
    # =========================================================
    def navigate_to(self, target_x, target_y):
        """Navigate to specific coordinates (for mission mode)"""
        self.navigation_mode = "MISSION"
        self.target_x = target_x
        self.target_y = target_y

        dx = target_x - self.drone.x
        dy = target_y - self.drone.y
        distance = math.sqrt(dx ** 2 + dy ** 2)

        if distance > 0.5:
            self.target_velocity_x = (dx / distance) * self.target_speed
            self.target_velocity_y = (dy / distance) * self.target_speed
        else:
            self.target_velocity_x = 0.0
            self.target_velocity_y = 0.0

    # =========================================================
    # AUTONOMOUS NAVIGATION (NEW)
    # =========================================================
    def set_autonomous_mode(self, enabled: bool):
        """Enable or disable autonomous mode"""
        self.autonomous_mode = enabled
        if enabled:
            self.navigation_mode = "AUTONOMOUS"
            print("🤖 Autonomous mode enabled")
        else:
            self.navigation_mode = "MANUAL"
            print("👤 Manual mode enabled")

    def set_target_heading(self, heading: float):
        """Set target heading for autonomous flight"""
        self.target_heading = heading % 360
        self.auto_heading_hold = True

    def follow_path(self, waypoints: list):
        """Load a path for autonomous following"""
        self.path_waypoints = waypoints
        self.current_path_index = 0
        self.path_following = True
        print(f"🛤️ Path loaded with {len(waypoints)} waypoints")

    def get_current_path_target(self):
        """Get the current path target waypoint"""
        if not self.path_following or self.current_path_index >= len(self.path_waypoints):
            return None
        return self.path_waypoints[self.current_path_index]

    def advance_path(self):
        """Advance to next path waypoint"""
        self.current_path_index += 1
        if self.current_path_index >= len(self.path_waypoints):
            self.path_following = False
            print("✅ Path complete")
            return False
        return True

    # =========================================================
    # OBSTACLE AVOIDANCE (NEW)
    # =========================================================
    def check_and_avoid_obstacles(self):
        """Check for obstacles and adjust course if needed"""
        if not self.obstacle_avoidance_enabled:
            return

        obstacles = self.drone.detected_obstacles
        if not obstacles:
            return

        for obstacle in obstacles:
            if obstacle['distance'] < self.avoidance_distance:
                # Calculate avoidance direction
                angle_rad = math.radians(obstacle['angle'] + self.avoidance_angle)
                avoid_x = math.cos(angle_rad) * self.target_speed
                avoid_y = math.sin(angle_rad) * self.target_speed
                
                # Apply avoidance
                self.target_velocity_x += avoid_x * 0.5
                self.target_velocity_y += avoid_y * 0.5
                
                print(f"⚠️ Obstacle avoided at {obstacle['distance']:.1f}m")
                break

    # =========================================================
    # STOP HORIZONTAL MOVEMENT
    # =========================================================
    def stop_horizontal(self):
        self.target_velocity_x = 0.0
        self.target_velocity_y = 0.0
        if self.drone.state in ["FLYING", "TAKING_OFF"]:
            self.navigation_mode = "HOLD"

    # =========================================================
    # TAKEOFF
    # =========================================================
    def start_takeoff(self):
        self.navigation_mode = "MANUAL"
        self.target_velocity_x = 0.0
        self.target_velocity_y = 0.0
        self.target_x = None
        self.target_y = None
        self.drone.velocity_z = 0.0
        
        # Reset PID controllers
        self.altitude_pid.reset()
        self.velocity_pid_x.reset()
        self.velocity_pid_y.reset()

    # =========================================================
    # LANDING
    # =========================================================
    def start_landing(self):
        self.navigation_mode = "LANDING"
        self.target_velocity_x = 0.0
        self.target_velocity_y = 0.0
        self.target_altitude = 0.0
        
        # Set PID target
        if self.use_pid:
            self.altitude_pid.setpoint = 0.0

    # =========================================================
    # RETURN HOME
    # =========================================================
    def return_home(self):
        if self.drone.state != "FLYING":
            return
        self.navigation_mode = "RETURN_HOME"
        self.target_x = self.drone.home_x
        self.target_y = self.drone.home_y
        if self.target_speed <= 0:
            self.target_speed = 5.0

    # =========================================================
    # EMERGENCY STOP
    # =========================================================
    def emergency_stop(self):
        self.navigation_mode = "EMERGENCY_STOP"
        self.target_velocity_x = 0.0
        self.target_velocity_y = 0.0
        self.target_altitude = self.drone.z
        self.drone.velocity_x = 0.0
        self.drone.velocity_y = 0.0
        self.drone.velocity_z = 0.0
        self.drone.acceleration_x = 0.0
        self.drone.acceleration_y = 0.0
        self.drone.acceleration_z = 0.0
        
        # Reset PID controllers
        self.altitude_pid.reset()
        self.velocity_pid_x.reset()
        self.velocity_pid_y.reset()

    # =========================================================
    # HOLD POSITION
    # =========================================================
    def hold_position(self):
        self.navigation_mode = "HOLD"
        self.target_velocity_x = 0.0
        self.target_velocity_y = 0.0
        self.target_altitude = self.drone.z
        
        if self.use_pid:
            self.altitude_pid.setpoint = self.drone.z

    # =========================================================
    # HORIZONTAL VELOCITY CONTROL
    # =========================================================
    def _approach_velocity(self, current, target, delta_time):
        difference = target - current

        if abs(difference) < 0.001:
            return target

        # Direction change - brake first
        if (current != 0 and target != 0 and
            ((current > 0 and target < 0) or (current < 0 and target > 0))):
            maximum_change = self.horizontal_deceleration * delta_time
        elif abs(target) > abs(current):
            maximum_change = self.horizontal_acceleration * delta_time
        else:
            maximum_change = self.horizontal_deceleration * delta_time

        if difference > 0:
            return min(current + maximum_change, target)
        return max(current - maximum_change, target)

    # =========================================================
    # VERTICAL VELOCITY CONTROL (PID version)
    # =========================================================
    def _approach_vertical_velocity_pid(self, current, target_altitude, delta_time):
        """Use PID controller for altitude control"""
        self.altitude_pid.setpoint = target_altitude
        return self.altitude_pid.update(current, delta_time)

    # =========================================================
    # VERTICAL VELOCITY CONTROL (Traditional)
    # =========================================================
    def _approach_vertical_velocity(self, current, target, delta_time):
        difference = target - current

        if abs(difference) < 0.001:
            return target

        if abs(target) > abs(current):
            maximum_change = self.vertical_acceleration * delta_time
        else:
            maximum_change = self.vertical_deceleration * delta_time

        if difference > 0:
            return min(current + maximum_change, target)
        return max(current - maximum_change, target)

    # =========================================================
    # CALCULATE TARGET VERTICAL VELOCITY
    # =========================================================
    def _calculate_vertical_target(self):
        altitude_error = self.target_altitude - self.drone.z

        if abs(altitude_error) <= self.altitude_threshold:
            return 0.0

        braking_velocity = math.sqrt(
            2 * self.vertical_deceleration * abs(altitude_error)
        )
        desired_speed = min(self.max_vertical_speed, braking_velocity)

        if altitude_error > 0:
            return desired_speed
        return -desired_speed

    # =========================================================
    # UPDATE CONTROLLER - COMPLETE
    # =========================================================
    def update(self, delta_time):
        # LANDED
        if self.drone.state == "LANDED":
            self.navigation_mode = "LANDED"
            self.target_velocity_x = 0.0
            self.target_velocity_y = 0.0
            self.target_altitude = 0.0
            self.drone.velocity_x = 0.0
            self.drone.velocity_y = 0.0
            self.drone.velocity_z = 0.0
            self.drone.acceleration_x = 0.0
            self.drone.acceleration_y = 0.0
            self.drone.acceleration_z = 0.0
            return

        # EMERGENCY STOP
        if self.navigation_mode == "EMERGENCY_STOP":
            self.drone.velocity_x = 0.0
            self.drone.velocity_y = 0.0
            self.drone.velocity_z = 0.0
            self.drone.acceleration_x = 0.0
            self.drone.acceleration_y = 0.0
            self.drone.acceleration_z = 0.0
            return

        # SAVE PREVIOUS VELOCITIES
        previous_velocity_x = self.drone.velocity_x
        previous_velocity_y = self.drone.velocity_y
        previous_velocity_z = self.drone.velocity_z

        # =====================================================
        # GEOFENCE RECOVERY - Highest priority
        # =====================================================
        if self.drone.geofence_breached:
            self.navigation_mode = "GEOFENCE_RECOVERY"
            direction = self.drone.geofence.get_safe_direction(
                self.drone.x, self.drone.y
            )
            target_speed = min(self.target_speed * 0.5, 5.0)
            self.target_velocity_x = direction[0] * target_speed
            self.target_velocity_y = direction[1] * target_speed

        # =====================================================
        # OBSTACLE AVOIDANCE (NEW)
        # =====================================================
        if self.obstacle_avoidance_enabled and self.drone.state == "FLYING":
            self.check_and_avoid_obstacles()

        # =====================================================
        # AUTONOMOUS PATH FOLLOWING (NEW)
        # =====================================================
        if self.path_following and self.drone.state == "FLYING":
            target = self.get_current_path_target()
            if target:
                self.navigate_to(target['x'], target['y'])
                # Check if reached target
                dx = target['x'] - self.drone.x
                dy = target['y'] - self.drone.y
                distance = math.sqrt(dx**2 + dy**2)
                if distance < self.arrival_threshold:
                    self.advance_path()

        # =====================================================
        # LANDING
        # =====================================================
        if self.drone.state == "LANDING":
            self.navigation_mode = "LANDING"
            self.target_velocity_x = 0.0
            self.target_velocity_y = 0.0

            self.drone.velocity_x = self._approach_velocity(
                previous_velocity_x, 0.0, delta_time
            )
            self.drone.velocity_y = self._approach_velocity(
                previous_velocity_y, 0.0, delta_time
            )

            if self.drone.z > 0.0:
                altitude_remaining = self.drone.z
                braking_velocity = math.sqrt(
                    2 * self.vertical_deceleration * altitude_remaining
                )
                desired_descent_speed = min(self.landing_speed, braking_velocity)
                target_vertical_velocity = -desired_descent_speed
            else:
                target_vertical_velocity = 0.0

            self.drone.velocity_z = self._approach_vertical_velocity(
                previous_velocity_z, target_vertical_velocity, delta_time
            )

            # Calculate acceleration
            if delta_time > 0:
                self.drone.acceleration_x = (self.drone.velocity_x - previous_velocity_x) / delta_time
                self.drone.acceleration_y = (self.drone.velocity_y - previous_velocity_y) / delta_time
                self.drone.acceleration_z = (self.drone.velocity_z - previous_velocity_z) / delta_time
            return

        # =====================================================
        # VERTICAL ALTITUDE CONTROL
        # =====================================================
        if self.use_pid:
            # Use PID for smooth altitude control
            vertical_velocity = self._approach_vertical_velocity_pid(
                self.drone.z, self.target_altitude, delta_time
            )
            self.drone.velocity_z = vertical_velocity
        else:
            # Use traditional method
            target_vertical_velocity = self._calculate_vertical_target()
            self.drone.velocity_z = self._approach_vertical_velocity(
                previous_velocity_z, target_vertical_velocity, delta_time
            )

        # =====================================================
        # RETURN HOME
        # =====================================================
        if (self.navigation_mode == "RETURN_HOME" and
            self.target_x is not None and
            self.target_y is not None):
            
            x_error = self.target_x - self.drone.x
            y_error = self.target_y - self.drone.y
            distance = math.sqrt(x_error ** 2 + y_error ** 2)

            if distance <= self.arrival_threshold:
                self.target_velocity_x = 0.0
                self.target_velocity_y = 0.0
                self.drone.velocity_x = 0.0
                self.drone.velocity_y = 0.0
                self.drone.land()
                return

            direction_x = x_error / distance
            direction_y = y_error / distance
            self.target_velocity_x = direction_x * self.target_speed
            self.target_velocity_y = direction_y * self.target_speed

        # =====================================================
        # SMOOTH HORIZONTAL MOVEMENT
        # =====================================================
        if self.use_pid:
            # Use PID for smooth velocity control
            self.drone.velocity_x = self.velocity_pid_x.update(
                self.drone.velocity_x, delta_time
            ) + self.target_velocity_x * 0.5
            self.drone.velocity_y = self.velocity_pid_y.update(
                self.drone.velocity_y, delta_time
            ) + self.target_velocity_y * 0.5
        else:
            # Use traditional method
            self.drone.velocity_x = self._approach_velocity(
                previous_velocity_x, self.target_velocity_x, delta_time
            )
            self.drone.velocity_y = self._approach_velocity(
                previous_velocity_y, self.target_velocity_y, delta_time
            )

        # =====================================================
        # CALCULATE ACCELERATION
        # =====================================================
        if delta_time > 0:
            self.drone.acceleration_x = (self.drone.velocity_x - previous_velocity_x) / delta_time
            self.drone.acceleration_y = (self.drone.velocity_y - previous_velocity_y) / delta_time
            self.drone.acceleration_z = (self.drone.velocity_z - previous_velocity_z) / delta_time
        else:
            self.drone.acceleration_x = 0.0
            self.drone.acceleration_y = 0.0
            self.drone.acceleration_z = 0.0

    # =========================================================
    # GET CONTROLLER STATUS (NEW)
    # =========================================================
    def get_status(self):
        """Get current controller status"""
        return {
            "navigation_mode": self.navigation_mode,
            "target_altitude": self.target_altitude,
            "target_speed": self.target_speed,
            "target_velocity_x": self.target_velocity_x,
            "target_velocity_y": self.target_velocity_y,
            "target_x": self.target_x,
            "target_y": self.target_y,
            "autonomous_mode": self.autonomous_mode,
            "path_following": self.path_following,
            "path_progress": f"{self.current_path_index}/{len(self.path_waypoints)}" if self.path_waypoints else "0/0",
            "use_pid": self.use_pid,
            "obstacle_avoidance": self.obstacle_avoidance_enabled,
            "altitude_pid": {
                "kp": self.altitude_pid.kp,
                "ki": self.altitude_pid.ki,
                "kd": self.altitude_pid.kd,
                "integral": self.altitude_pid.integral,
                "error": self.altitude_pid.setpoint - self.drone.z
            }
        }