import time
import math
import random
from simulator.core.wind import WindSystem
from simulator.core.terrain import TerrainGenerator
from simulator.core.signal import SignalSimulator
from simulator.core.emergency import EmergencySystem


class Geofence:
    """Geofence boundary enforcement for drone safety"""
    
    def __init__(self, center_x=0.0, center_y=0.0, radius=100.0):
        self.center_x = center_x
        self.center_y = center_y
        self.radius = radius
        self.breach_threshold = 0.85
        
    def check_position(self, x, y):
        distance = math.sqrt((x - self.center_x) ** 2 + (y - self.center_y) ** 2)
        is_breached = distance > self.radius
        is_warning = distance > self.radius * self.breach_threshold and not is_breached
        
        return {
            "distance": round(distance, 2),
            "is_breached": is_breached,
            "is_warning": is_warning,
            "distance_percentage": round((distance / self.radius) * 100, 2) if self.radius > 0 else 0
        }
    
    def get_safe_direction(self, x, y):
        dx = self.center_x - x
        dy = self.center_y - y
        distance = math.sqrt(dx * dx + dy * dy)
        
        if distance < 0.01:
            return (0.0, 0.0)
        
        return (dx / distance, dy / distance)


class Drone:
    def __init__(self):
        # ====================================================
        # POSITION
        # ====================================================
        self.x = 0.0
        self.y = 0.0
        self.z = 0.0

        # ====================================================
        # HOME POSITION
        # ====================================================
        self.home_x = 0.0
        self.home_y = 0.0
        self.home_z = 0.0

        # ====================================================
        # VELOCITY
        # ====================================================
        self.velocity_x = 0.0
        self.velocity_y = 0.0
        self.velocity_z = 0.0

        # ====================================================
        # ACCELERATION
        # ====================================================
        self.acceleration_x = 0.0
        self.acceleration_y = 0.0
        self.acceleration_z = 0.0

        # ====================================================
        # DRONE TILT (for visualization)
        # ====================================================
        self.tilt_roll = 0.0  # Degrees - side to side
        self.tilt_pitch = 0.0  # Degrees - forward/backward
        
        # ====================================================
        # FLIGHT LIMITS
        # ====================================================
        self.ground_level = 0.0
        self.max_altitude = 120.0
        self.max_speed = 30.0
        self.max_vertical_speed = 5.0
        self.max_tilt = 35.0  # Maximum tilt angle in degrees

        # ====================================================
        # SAFETY ALTITUDE
        # ====================================================
        self.low_altitude_threshold = 5.0

        # ====================================================
        # FLIGHT STATE
        # ====================================================
        self.state = "LANDED"

        # ====================================================
        # FLIGHT TIME
        # ====================================================
        self.flight_start_time = None
        self.total_flight_time = 0.0

        # ====================================================
        # DISTANCE TRACKING
        # ====================================================
        self.distance_travelled = 0.0

        # ====================================================
        # BATTERY - ENHANCED
        # ====================================================
        self.battery = 100.0
        self.max_battery = 100.0
        self.battery_temperature = 25.0  # Celsius
        self.battery_health = 100.0  # Degradation over time
        
        # Battery consumption rates (mAh per second)
        self.battery_drain_hover = 0.008
        self.battery_drain_cruise = 0.015
        self.battery_drain_full = 0.025
        
        # ====================================================
        # GEOFENCE
        # ====================================================
        self.geofence = Geofence(radius=100.0)
        self.geofence_breached = False
        self.geofence_warning = False
        
        # ====================================================
        # WIND SYSTEM
        # ====================================================
        self.wind = WindSystem()
        self.wind_effect_x = 0.0
        self.wind_effect_y = 0.0
        
        # ====================================================
        # TERRAIN & OBSTACLES
        # ====================================================
        self.terrain = TerrainGenerator()
        self.terrain.generate_height_map()
        self.terrain.generate_obstacles()
        self.terrain.generate_no_fly_zones()
        self.terrain_awareness = True  # Enable terrain following
        
        # ====================================================
        # SIGNAL SIMULATION
        # ====================================================
        self.signal = SignalSimulator(max_range=500)
        self.signal.add_interference_zone(30, 20, 30, 0.3)  # Add some interference
        self.signal.add_interference_zone(-20, -30, 25, 0.4)
        
        # ====================================================
        # EMERGENCY SYSTEM
        # ====================================================
        self.emergency = EmergencySystem(self, None)  # Controller will be set later
        self.emergency_active = False
        self.emergency_type = None
        
        # ====================================================
        # MISSION RECORDING
        # ====================================================
        self.recording = False
        self.recording_data = []
        self.recording_start_time = None

    # ========================================================
    # TAKEOFF
    # ========================================================
    def takeoff(self):
        if self.state == "LANDED":
            self.state = "TAKING_OFF"
            self.flight_start_time = time.time()
            self.total_flight_time = 0.0
            self.distance_travelled = 0.0
            self.geofence_breached = False
            self.geofence_warning = False
            self.battery_health = max(80.0, self.battery_health - 0.1)
            self.emergency_active = False
            self.emergency_type = None
            print("Drone is taking off...")
            return True
        return False

    # ========================================================
    # LAND
    # ========================================================
    def land(self):
        if self.state in ["FLYING", "TAKING_OFF"]:
            self.state = "LANDING"
            print("Drone is landing...")
            return True
        return False

    # ========================================================
    # SET CONTROLLER REFERENCE
    # ========================================================
    def set_controller(self, controller):
        """Set the flight controller reference for emergency system"""
        self.emergency.controller = controller

    # ========================================================
    # UPDATE PHYSICS - WITH ALL ENHANCEMENTS
    # ========================================================
    def update(self, delta_time):
        if self.state == "LANDED":
            return

        # Check for emergencies
        if not self.emergency_active:
            self.emergency.check_emergencies(delta_time)
            if self.emergency.emergency_active:
                self.emergency_active = True
                self.emergency_type = self.emergency.emergency_type
                print(f"⚠️ EMERGENCY: {self.emergency_type}")

        # Flight time
        if self.flight_start_time is not None:
            self.total_flight_time = time.time() - self.flight_start_time

        # Previous position for distance tracking
        previous_x = self.x
        previous_y = self.y

        # ====================================================
        # WIND EFFECTS
        # ====================================================
        if self.state in ["FLYING", "TAKING_OFF", "LANDING"]:
            wind_x, wind_y = self.wind.get_wind_vector(time.time(), self.z)
            self.wind_effect_x = wind_x
            self.wind_effect_y = wind_y
            
            # Apply wind to velocity (with some inertia)
            wind_influence = 0.02 * delta_time * 20
            self.velocity_x += (wind_x - self.velocity_x * 0.1) * wind_influence
            self.velocity_y += (wind_y - self.velocity_y * 0.1) * wind_influence

        # Position update
        self.x += self.velocity_x * delta_time
        self.y += self.velocity_y * delta_time
        self.z += self.velocity_z * delta_time

        # Distance travelled
        horizontal_distance = math.sqrt(
            (self.x - previous_x) ** 2 + (self.y - previous_y) ** 2
        )
        self.distance_travelled += horizontal_distance

        # ====================================================
        # TERRAIN & OBSTACLE AWARENESS
        # ====================================================
        if self.terrain_awareness and self.state in ["FLYING", "TAKING_OFF"]:
            safe, reason, data = self.check_terrain_safety(self.x, self.y, self.z)
            
            if not safe:
                if reason == "OBSTACLE":
                    # Climb above obstacle
                    target_alt = data["height"] + 5
                    if self.z < target_alt:
                        self.velocity_z = min(self.velocity_z + 2, self.max_vertical_speed)
                        print(f"⚠️ Obstacle detected! Climbing to {target_alt}m")
                        
                elif reason == "TERRAIN":
                    # Follow terrain
                    target_z = data + 3  # Stay 3m above ground
                    if self.z < target_z:
                        self.velocity_z = min(self.velocity_z + 1, self.max_vertical_speed)
                        
                elif reason == "NO_FLY_ZONE":
                    # Turn away from no-fly zone
                    dx = self.x - data["x"]
                    dy = self.y - data["y"]
                    distance = math.sqrt(dx**2 + dy**2)
                    if distance > 0:
                        self.velocity_x = (dx / distance) * 5
                        self.velocity_y = (dy / distance) * 5
                        print(f"⚠️ No-fly zone detected! Evading...")

        # ====================================================
        # DRONE TILT CALCULATION
        # ====================================================
        self._calculate_tilt(delta_time)

        # ====================================================
        # GEOFENCE ENFORCEMENT
        # ====================================================
        geofence_status = self.geofence.check_position(self.x, self.y)
        self.geofence_breached = geofence_status["is_breached"]
        self.geofence_warning = geofence_status["is_warning"]
        
        if geofence_status["is_breached"]:
            direction = self.geofence.get_safe_direction(self.x, self.y)
            target_x = direction[0] * min(self.get_horizontal_speed(), 5.0)
            target_y = direction[1] * min(self.get_horizontal_speed(), 5.0)
            self.velocity_x += (target_x - self.velocity_x) * 0.1
            self.velocity_y += (target_y - self.velocity_y) * 0.1
            
            if geofence_status["distance"] < 1.0:
                self.x = self.geofence.center_x
                self.y = self.geofence.center_y
                self.velocity_x = 0.0
                self.velocity_y = 0.0
                self.geofence_breached = False

        # ====================================================
        # GROUND COLLISION
        # ====================================================
        if self.z <= self.ground_level:
            self.z = self.ground_level
            self.velocity_x = 0.0
            self.velocity_y = 0.0
            self.velocity_z = 0.0

            if self.state == "LANDING":
                self.state = "LANDED"
                if self.flight_start_time is not None:
                    self.total_flight_time = time.time() - self.flight_start_time
                    self.flight_start_time = None
                print("Drone has landed.")
                return

        # ====================================================
        # MAXIMUM ALTITUDE
        # ====================================================
        if self.z >= self.max_altitude:
            self.z = self.max_altitude
            if self.velocity_z > 0:
                self.velocity_z = 0.0

        # ====================================================
        # MAXIMUM HORIZONTAL SPEED
        # ====================================================
        horizontal_speed = self.get_horizontal_speed()
        if horizontal_speed > self.max_speed:
            scale = self.max_speed / horizontal_speed
            self.velocity_x *= scale
            self.velocity_y *= scale

        # ====================================================
        # MAXIMUM VERTICAL SPEED
        # ====================================================
        if self.velocity_z > self.max_vertical_speed:
            self.velocity_z = self.max_vertical_speed
        if self.velocity_z < -self.max_vertical_speed:
            self.velocity_z = -self.max_vertical_speed

        # ====================================================
        # TAKEOFF STATE
        # ====================================================
        if self.state == "TAKING_OFF" and self.z > 1.0:
            self.state = "FLYING"
            print("Drone is now flying!")

        # ====================================================
        # BATTERY CONSUMPTION - ENHANCED
        # ====================================================
        self._update_battery(delta_time)
        
        # Check battery critical emergency
        if self.battery < 10 and not self.emergency_active:
            self.emergency.trigger_emergency("battery_critical")
            self.emergency_active = True
            self.emergency_type = "battery_critical"
            print("⚠️ CRITICAL BATTERY! Emergency landing initiated...")

        # ====================================================
        # RECORD MISSION DATA
        # ====================================================
        if self.recording:
            self._record_frame()

    # ========================================================
    # TERRAIN SAFETY CHECK
    # ========================================================
    def check_terrain_safety(self, x, y, z):
        """Check if position is safe (not colliding with terrain/obstacles)"""
        terrain_info = self.terrain.get_terrain_info(x, y)
        
        if terrain_info["in_no_fly_zone"]:
            return False, "NO_FLY_ZONE", terrain_info["no_fly_zone"]
        
        if terrain_info["has_obstacle"] and z < terrain_info["obstacle"]["height"]:
            return False, "OBSTACLE", terrain_info["obstacle"]
        
        if z < terrain_info["height"]:
            return False, "TERRAIN", terrain_info["height"]
        
        return True, "SAFE", None

    # ========================================================
    # SIGNAL STRENGTH
    # ========================================================
    def get_signal_strength(self):
        """Get current signal strength from ground station"""
        return self.signal.get_signal_strength(
            self.x, self.y, self.z,
            self.home_x, self.home_y
        )

    # ========================================================
    # MISSION RECORDING
    # ========================================================
    def start_recording(self):
        """Start recording mission data"""
        self.recording = True
        self.recording_data = []
        self.recording_start_time = time.time()
        print("📹 Mission recording started")
        return True

    def stop_recording(self):
        """Stop recording mission data"""
        self.recording = False
        print(f"📹 Mission recording stopped. {len(self.recording_data)} frames recorded")
        return self.recording_data

    def _record_frame(self):
        """Record a single frame of drone data"""
        if not self.recording:
            return
            
        frame = {
            "timestamp": time.time() - self.recording_start_time,
            "position": {"x": self.x, "y": self.y, "z": self.z},
            "velocity": {"x": self.velocity_x, "y": self.velocity_y, "z": self.velocity_z},
            "speed": {"horizontal": self.get_horizontal_speed()},
            "battery": self.battery,
            "state": self.state,
            "altitude": {"current": self.z}
        }
        self.recording_data.append(frame)

    # ========================================================
    # DRONE TILT CALCULATION
    # ========================================================
    def _calculate_tilt(self, delta_time):
        """Calculate drone tilt based on velocity and acceleration"""
        horizontal_speed = self.get_horizontal_speed()
        max_tilt = self.max_tilt
        
        # Tilt based on horizontal speed (smooth transition)
        speed_ratio = min(horizontal_speed / self.max_speed, 1.0)
        tilt_magnitude = speed_ratio * max_tilt
        
        # Calculate tilt direction
        if horizontal_speed > 0.1:
            # Tilt in direction of movement
            angle = math.atan2(self.velocity_y, self.velocity_x)
            target_pitch = tilt_magnitude * math.cos(angle)
            target_roll = -tilt_magnitude * math.sin(angle)
        else:
            target_pitch = 0.0
            target_roll = 0.0
        
        # Smooth tilt transitions
        smooth_factor = 0.15 * delta_time * 20
        self.tilt_pitch += (target_pitch - self.tilt_pitch) * smooth_factor
        self.tilt_roll += (target_roll - self.tilt_roll) * smooth_factor
        
        # Add small hover oscillation
        if self.state == "FLYING" and horizontal_speed < 0.5:
            hover_osc = math.sin(time.time() * 0.5) * 0.5
            self.tilt_roll += hover_osc * 0.1
            self.tilt_pitch += math.cos(time.time() * 0.7) * 0.1

    # ========================================================
    # BATTERY UPDATE - ENHANCED
    # ========================================================
    def _update_battery(self, delta_time):
        """Realistic battery consumption with temperature and load effects"""
        if self.state == "LANDED":
            return
            
        horizontal_speed = self.get_horizontal_speed()
        vertical_speed = abs(self.velocity_z)
        
        # Base drain rate
        if horizontal_speed < 0.5 and vertical_speed < 0.5:
            # Hovering
            drain_rate = self.battery_drain_hover
        elif horizontal_speed < 15.0:
            # Cruising
            drain_rate = self.battery_drain_cruise + (horizontal_speed / 30) * 0.005
        else:
            # Full speed
            drain_rate = self.battery_drain_full + (horizontal_speed / 30) * 0.01
            
        # Additional drain for vertical movement
        drain_rate += vertical_speed * 0.002
        
        # Temperature effects (battery drains faster when hot)
        temp_factor = 1 + (self.battery_temperature - 25) * 0.01
        drain_rate *= max(0.5, min(2.0, temp_factor))
        
        # Battery health degradation
        health_factor = self.battery_health / 100.0
        drain_rate *= (1 + (1 - health_factor) * 0.5)
        
        # Apply drain
        self.battery -= drain_rate * delta_time
        
        # Update battery temperature
        self._update_battery_temperature(delta_time, drain_rate)
        
        # Prevent negative battery
        if self.battery < 0.0:
            self.battery = 0.0
            
    def _update_battery_temperature(self, delta_time, drain_rate):
        """Simulate battery temperature changes"""
        # Heat generation from discharge
        heat_generation = drain_rate * 2.0
        
        # Cooling (approaches ambient)
        ambient_temp = 25.0
        cooling = (self.battery_temperature - ambient_temp) * 0.01
        
        # Temperature change
        self.battery_temperature += (heat_generation - cooling) * delta_time
        self.battery_temperature = max(15, min(50, self.battery_temperature))

    # ========================================================
    # HORIZONTAL SPEED
    # ========================================================
    def get_horizontal_speed(self):
        return math.sqrt(self.velocity_x ** 2 + self.velocity_y ** 2)

    # ========================================================
    # TOTAL SPEED
    # ========================================================
    def get_total_speed(self):
        return math.sqrt(
            self.velocity_x ** 2 +
            self.velocity_y ** 2 +
            self.velocity_z ** 2
        )

    # ========================================================
    # DISTANCE FROM HOME
    # ========================================================
    def get_distance_from_home(self):
        return math.sqrt(
            (self.x - self.home_x) ** 2 +
            (self.y - self.home_y) ** 2 +
            (self.z - self.home_z) ** 2
        )

    # ========================================================
    # ALTITUDE PERCENTAGE
    # ========================================================
    def get_altitude_percentage(self):
        if self.max_altitude <= 0:
            return 0.0
        percentage = (self.z / self.max_altitude) * 100.0
        return max(0.0, min(percentage, 100.0))

    # ========================================================
    # ALTITUDE WARNING
    # ========================================================
    def get_altitude_warning(self):
        if self.z <= self.ground_level:
            return "GROUND"
        if self.z <= self.low_altitude_threshold:
            return "LOW_ALTITUDE"
        if self.z >= (self.max_altitude * 0.9):
            return "HIGH_ALTITUDE"
        return "NORMAL"

    # ========================================================
    # GET DRONE STATUS - ENHANCED
    # ========================================================
    def get_status(self):
        horizontal_speed = self.get_horizontal_speed()
        total_speed = self.get_total_speed()
        distance_from_home = self.get_distance_from_home()
        altitude_percentage = self.get_altitude_percentage()
        altitude_warning = self.get_altitude_warning()
        geofence_status = self.geofence.check_position(self.x, self.y)
        signal_status = self.get_signal_strength()
        
        # Terrain info at current position
        terrain_info = self.terrain.get_terrain_info(self.x, self.y)

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
            "speed": {
                "horizontal": round(horizontal_speed, 2),
                "vertical": round(abs(self.velocity_z), 2),
                "total": round(total_speed, 2)
            },
            "acceleration": {
                "x": round(self.acceleration_x, 2),
                "y": round(self.acceleration_y, 2),
                "z": round(self.acceleration_z, 2)
            },
            "battery": round(self.battery, 2),
            "battery_temperature": round(self.battery_temperature, 1),
            "battery_health": round(self.battery_health, 1),
            "flight_time": round(self.total_flight_time, 2),
            "distance_travelled": round(self.distance_travelled, 2),
            "distance_from_home": round(distance_from_home, 2),
            "altitude": {
                "current": round(self.z, 2),
                "ground_level": round(self.ground_level, 2),
                "maximum": round(self.max_altitude, 2),
                "percentage": round(altitude_percentage, 2),
                "warning": altitude_warning
            },
            "limits": {
                "ground_level": self.ground_level,
                "max_altitude": self.max_altitude,
                "max_speed": self.max_speed,
                "max_vertical_speed": self.max_vertical_speed
            },
            "geofence": {
                "radius": self.geofence.radius,
                "distance_from_center": geofence_status["distance"],
                "is_breached": geofence_status["is_breached"],
                "is_warning": geofence_status["is_warning"],
                "distance_percentage": geofence_status["distance_percentage"]
            },
            "wind": {
                "speed_x": round(self.wind_effect_x, 2),
                "speed_y": round(self.wind_effect_y, 2),
                "description": self.wind.get_wind_description()
            },
            "tilt": {
                "roll": round(self.tilt_roll, 1),
                "pitch": round(self.tilt_pitch, 1)
            },
            "terrain": {
                "ground_height": round(terrain_info["height"], 2),
                "has_obstacle": terrain_info["has_obstacle"],
                "in_no_fly_zone": terrain_info["in_no_fly_zone"]
            },
            "signal": {
                "strength": signal_status["strength"],
                "quality": signal_status["quality"],
                "latency": signal_status["latency"],
                "distance": signal_status["distance"],
                "signal_lost": signal_status["strength"] < 0.1
            },
            "emergency": {
                "active": self.emergency_active,
                "type": self.emergency_type if self.emergency_active else None
            },
            "recording": self.recording
        }