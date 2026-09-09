import math


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
        self.navigation_mode = "MANUAL"  # MANUAL, HOLD, LANDING, RETURN_HOME, MISSION, GEOFENCE_RECOVERY
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

    # =========================================================
    # ALTITUDE
    # =========================================================
    def set_altitude(self, altitude):
        altitude = max(0.0, altitude)
        altitude = min(altitude, self.drone.max_altitude)
        self.target_altitude = altitude

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

    # =========================================================
    # LANDING
    # =========================================================
    def start_landing(self):
        self.navigation_mode = "LANDING"
        self.target_velocity_x = 0.0
        self.target_velocity_y = 0.0
        self.target_altitude = 0.0

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

    # =========================================================
    # HOLD POSITION
    # =========================================================
    def hold_position(self):
        self.navigation_mode = "HOLD"
        self.target_velocity_x = 0.0
        self.target_velocity_y = 0.0
        self.target_altitude = self.drone.z

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
    # VERTICAL VELOCITY CONTROL
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
    # UPDATE CONTROLLER
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
            # Slow down and return to center
            target_speed = min(self.target_speed * 0.5, 5.0)
            self.target_velocity_x = direction[0] * target_speed
            self.target_velocity_y = direction[1] * target_speed

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