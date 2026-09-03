class Drone:

    def __init__(self):

        # =========================
        # POSITION
        # =========================

        self.x = 0.0
        self.y = 0.0
        self.z = 0.0


        # =========================
        # VELOCITY
        # =========================

        self.velocity_x = 0.0
        self.velocity_y = 0.0
        self.velocity_z = 0.0


        # =========================
        # ACCELERATION
        # =========================

        self.acceleration_x = 0.0
        self.acceleration_y = 0.0
        self.acceleration_z = 0.0


        # =========================
        # LIMITS
        # =========================

        self.max_altitude = 120.0
        self.max_speed = 30.0


        # =========================
        # FLIGHT STATE
        # =========================

        self.state = "LANDED"


        # =========================
        # BATTERY
        # =========================

        self.battery = 100.0


    # =========================
    # TAKEOFF
    # =========================

    def takeoff(self):

        if self.state == "LANDED":

            self.state = "TAKING_OFF"

            print("Drone is taking off...")


    # =========================
    # LAND
    # =========================

    def land(self):

        if self.state in ["FLYING", "TAKING_OFF"]:

            self.state = "LANDING"

            print("Drone is landing...")


    # =========================
    # UPDATE PHYSICS
    # =========================

    def update(self, delta_time):

        if self.state == "LANDED":

            return


        # --------------------------------
        # UPDATE POSITION
        # --------------------------------

        self.x += self.velocity_x * delta_time

        self.y += self.velocity_y * delta_time

        self.z += self.velocity_z * delta_time


        # --------------------------------
        # GROUND LIMIT
        # --------------------------------

        if self.z <= 0:

            self.z = 0.0

            self.velocity_z = 0.0

            if self.state == "LANDING":

                self.state = "LANDED"


        # --------------------------------
        # MAX ALTITUDE
        # --------------------------------

        if self.z >= self.max_altitude:

            self.z = self.max_altitude

            self.velocity_z = 0.0


        # --------------------------------
        # TAKEOFF STATE
        # --------------------------------

        if self.state == "TAKING_OFF" and self.z > 1:

            self.state = "FLYING"


        # --------------------------------
        # BATTERY
        # --------------------------------

        self.battery -= 0.01 * delta_time

        if self.battery < 0:

            self.battery = 0.0


    # =========================
    # STATUS
    # =========================

    def get_status(self):

        return {

            "state": self.state,

            "position": {

                "x": round(self.x, 2),

                "y": round(self.y, 2),

                "z": round(self.z, 2)

            },

            "velocity": {

                "x": round(self.velocity_x, 2),

                "y": round(self.velocity_y, 2),

                "z": round(self.velocity_z, 2)

            },

            "battery": round(self.battery, 2)

        }