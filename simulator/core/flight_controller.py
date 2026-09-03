class FlightController:

    def __init__(self, drone):

        self.drone = drone

        # Pilot targets
        self.target_altitude = 0.0
        self.target_speed = 0.0

        # Movement commands
        self.target_velocity_x = 0.0
        self.target_velocity_y = 0.0

    # =========================
    # SET TARGET ALTITUDE
    # =========================

    def set_altitude(self, altitude):

        if altitude < 0:
            altitude = 0

        if altitude > self.drone.max_altitude:
            altitude = self.drone.max_altitude

        self.target_altitude = altitude

    # =========================
    # SET TARGET SPEED
    # =========================

    def set_speed(self, speed):

        if speed < 0:
            speed = 0

        if speed > self.drone.max_speed:
            speed = self.drone.max_speed

        self.target_speed = speed

    # =========================
    # MOVE FORWARD
    # =========================

    def move_forward(self):

        self.target_velocity_x = self.target_speed

    # =========================
    # MOVE BACKWARD
    # =========================

    def move_backward(self):

        self.target_velocity_x = -self.target_speed

    # =========================
    # MOVE RIGHT
    # =========================

    def move_right(self):

        self.target_velocity_y = self.target_speed

    # =========================
    # MOVE LEFT
    # =========================

    def move_left(self):

        self.target_velocity_y = -self.target_speed

    # =========================
    # STOP HORIZONTAL MOVEMENT
    # =========================

    def stop_horizontal(self):

        self.target_velocity_x = 0.0
        self.target_velocity_y = 0.0

    # =========================
    # UPDATE CONTROLLER
    # =========================

    def update(self, delta_time):

        # --------------------------------
        # ALTITUDE CONTROL
        # --------------------------------

        altitude_error = (
            self.target_altitude - self.drone.z
        )

        altitude_speed = 5.0

        if abs(altitude_error) < 0.5:

            self.drone.velocity_z = 0.0

        elif altitude_error > 0:

            self.drone.velocity_z = altitude_speed

        else:

            self.drone.velocity_z = -altitude_speed


        # --------------------------------
        # HORIZONTAL CONTROL
        # --------------------------------

        self.drone.velocity_x = self.target_velocity_x
        self.drone.velocity_y = self.target_velocity_y