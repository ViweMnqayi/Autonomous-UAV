import time
import math
import random
from datetime import datetime
from simulator.core.wind import WindSystem
from simulator.core.terrain import TerrainGenerator
from simulator.core.signal import SignalSimulator
from simulator.core.emergency import EmergencySystem
from simulator.core.physics import PhysicsEngine
from simulator.core.sensors import GPS, IMU, Barometer, Magnetometer
from simulator.core.pid import PID, AltitudeController, VelocityController
from simulator.core.data_storage import TelemetryStorage
from simulator.core.vision import VisionSystem


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
        self.signal.add_interference_zone(30, 20, 30, 0.3)
        self.signal.add_interference_zone(-20, -30, 25, 0.4)
        
        # ====================================================
        # EMERGENCY SYSTEM
        # ====================================================
        self.emergency = EmergencySystem(self, None)
        self.emergency_active = False
        self.emergency_type = None
        
        # ====================================================
        # MISSION RECORDING
        # ====================================================
        self.recording = False
        self.recording_data = []
        self.recording_start_time = None
        self.flight_id = None

        # ====================================================
        # PHYSICS ENGINE (NEW)
        # ====================================================
        self.physics = PhysicsEngine()
        self.throttle = 0.0  # 0-1 throttle value
        
        # ====================================================
        # SENSOR SUITE (NEW)
        # ====================================================
        self.gps = GPS(noise_level=0.5, drift_rate=0.01)
        self.imu = IMU()
        self.barometer = Barometer(noise_level=0.3)
        self.magnetometer = Magnetometer(noise_level=0.5)
        
        # Sensor readings (updated each frame)
        self.gps_position = (0.0, 0.0, 0.0)
        self.imu_data = {"acceleration": (0, 0, 0), "gyroscope": (0, 0, 0)}
        self.barometer_altitude = 0.0
        self.magnetometer_heading = 0.0
        
        # ====================================================
        # PID CONTROLLERS (NEW)
        # ====================================================
        self.altitude_controller = AltitudeController(self)
        self.velocity_controller = VelocityController(self)
        
        # ====================================================
        # DATA STORAGE (NEW)
        # ====================================================
        self.storage = TelemetryStorage()
        self.is_recording_to_db = False
        
        # ====================================================
        # VISION SYSTEM (NEW)
        # ====================================================
        self.vision = VisionSystem(detection_range=50.0, field_of_view=60)
        self.detected_obstacles = []
        self.detected_landing_zone = None

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
            self.flight_id = datetime.now().strftime("%Y%m%d_%H%M%S")
            print(f"Drone is taking off... (Flight ID: {self.flight_id})")
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
        self.emergency.controller = controller

    # ========================================================
    # UPDATE PHYSICS - COMPLETE WITH ALL SYSTEMS
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

        # ====================================================
        # ADVANCED PHYSICS (NEW)
        # ====================================================
        if self.state in ["FLYING", "TAKING_OFF", "LANDING"]:
            # Calculate physics-based accelerations
            target_pitch = self.tilt_pitch
            target_roll = self.tilt_roll
            target_yaw = 0.0
            
            # Update physics engine
            accel_x, accel_y, accel_z = self.physics.update_dynamics(
                self.velocity_x, self.velocity_y, self.velocity_z,
                self.throttle,
                self.z,
                target_pitch, target_roll, target_yaw,
                delta_time
            )
            
            # Apply physics accelerations
            self.acceleration_x = accel_x
            self.acceleration_y = accel_y
            self.acceleration_z = accel_z
            
            # Update velocity from physics
            self.velocity_x += accel_x * delta_time
            self.velocity_y += accel_y * delta_time
            self.velocity_z += accel_z * delta_time

        # ====================================================
        # POSITION UPDATE
        # ====================================================
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
                    target_alt = data["height"] + 5
                    if self.z < target_alt:
                        self.velocity_z = min(self.velocity_z + 2, self.max_vertical_speed)
                        print(f"⚠️ Obstacle detected! Climbing to {target_alt}m")
                        
                elif reason == "TERRAIN":
                    target_z = data + 3
                    if self.z < target_z:
                        self.velocity_z = min(self.velocity_z + 1, self.max_vertical_speed)
                        
                elif reason == "NO_FLY_ZONE":
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
                # Save flight summary to database
                if self.flight_id:
                    self._save_flight_summary()
                return

        # ====================================================
        # MAXIMUM ALTITUDE
        # ====================================================
        if self.z >= self.max_altitude:
            self.z = self.max_altitude
            if self.velocity_z > 0:
                self.velocity_z = 0.0

        # ====================================================
        # MAXIMUM SPEED LIMITS
        # ====================================================
        horizontal_speed = self.get_horizontal_speed()
        if horizontal_speed > self.max_speed:
            scale = self.max_speed / horizontal_speed
            self.velocity_x *= scale
            self.velocity_y *= scale

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
        # BATTERY CONSUMPTION
        # ====================================================
        self._update_battery(delta_time)
        
        # Check battery critical emergency
        if self.battery < 10 and not self.emergency_active:
            self.emergency.trigger_emergency("battery_critical")
            self.emergency_active = True
            self.emergency_type = "battery_critical"
            print("⚠️ CRITICAL BATTERY! Emergency landing initiated...")

        # ====================================================
        # SENSOR UPDATES (NEW)
        # ====================================================
        self._update_sensors(delta_time)

        # ====================================================
        # VISION SYSTEM UPDATE (NEW)
        # ====================================================
        self._update_vision()

        # ====================================================
        # RECORD MISSION DATA
        # ====================================================
        if self.recording:
            self._record_frame()
        
        # ====================================================
        # RECORD TO DATABASE (NEW)
        # ====================================================
        if self.is_recording_to_db and self.flight_id:
            self._save_telemetry_to_db()

    # ========================================================
    # SENSOR UPDATE (NEW)
    # ========================================================
    def _update_sensors(self, delta_time):
        """Update all sensor readings"""
        # GPS
        self.gps_position = self.gps.update(self.x, self.y, self.z, delta_time)
        
        # IMU
        true_accel = (self.acceleration_x, self.acceleration_y, self.acceleration_z)
        true_gyro = (0, 0, 0)  # Simplified for now
        self.imu_data = self.imu.update(true_accel, true_gyro)
        
        # Barometer
        self.barometer_altitude = self.barometer.update(self.z)
        
        # Magnetometer (heading from velocity)
        heading = math.degrees(math.atan2(self.velocity_y, self.velocity_x))
        self.magnetometer_heading = self.magnetometer.update(heading)

    # ========================================================
    # VISION SYSTEM UPDATE (NEW)
    # ========================================================
    def _update_vision(self):
        """Update vision system detections"""
        if self.state != "FLYING":
            return
            
        heading = math.degrees(math.atan2(self.velocity_y, self.velocity_x))
        
        # Detect obstacles
        self.detected_obstacles = self.vision.detect_obstacles(
            self.x, self.y, self.z,
            heading,
            self.terrain.obstacles
        )
        
        # Detect landing zone
        self.detected_landing_zone = self.vision.detect_landing_zone(
            self.terrain, self.x, self.y
        )

    # ========================================================
    # DATA STORAGE (NEW)
    # ========================================================
    def _save_telemetry_to_db(self):
        """Save current telemetry to database"""
        status = self.get_status()
        self.storage.save_telemetry(status, self.flight_id)

    def _save_flight_summary(self):
        """Save flight summary to database"""
        summary = {
            "start_time": self.flight_start_time or 0,
            "end_time": time.time(),
            "duration": self.total_flight_time,
            "distance": self.distance_travelled,
            "max_altitude": self.z,  # Could track max separately
            "max_speed": self.max_speed,
            "avg_battery": 80,  # Placeholder
            "waypoints": 0,  # Placeholder
            "status": self.state
        }
        self.storage.save_flight_summary(self.flight_id, summary)

    def start_db_recording(self):
        """Start recording telemetry to database"""
        if not self.flight_id:
            self.flight_id = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.is_recording_to_db = True
        print(f"📊 Database recording started for flight {self.flight_id}")

    def stop_db_recording(self):
        """Stop recording to database and save summary"""
        self.is_recording_to_db = False
        if self.flight_id:
            self._save_flight_summary()
            print(f"📊 Database recording stopped for flight {self.flight_id}")
        return self.flight_id

    # ========================================================
    # TERRAIN SAFETY CHECK
    # ========================================================
    def check_terrain_safety(self, x, y, z):
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
        return self.signal.get_signal_strength(
            self.x, self.y, self.z,
            self.home_x, self.home_y
        )

    # ========================================================
    # MISSION RECORDING
    # ========================================================
    def start_recording(self):
        self.recording = True
        self.recording_data = []
        self.recording_start_time = time.time()
        print("📹 Mission recording started")
        return True

    def stop_recording(self):
        self.recording = False
        print(f"📹 Mission recording stopped. {len(self.recording_data)} frames recorded")
        return self.recording_data

    def _record_frame(self):
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
        horizontal_speed = self.get_horizontal_speed()
        max_tilt = self.max_tilt
        
        speed_ratio = min(horizontal_speed / self.max_speed, 1.0)
        tilt_magnitude = speed_ratio * max_tilt
        
        if horizontal_speed > 0.1:
            angle = math.atan2(self.velocity_y, self.velocity_x)
            target_pitch = tilt_magnitude * math.cos(angle)
            target_roll = -tilt_magnitude * math.sin(angle)
        else:
            target_pitch = 0.0
            target_roll = 0.0
        
        smooth_factor = 0.15 * delta_time * 20
        self.tilt_pitch += (target_pitch - self.tilt_pitch) * smooth_factor
        self.tilt_roll += (target_roll - self.tilt_roll) * smooth_factor
        
        if self.state == "FLYING" and horizontal_speed < 0.5:
            hover_osc = math.sin(time.time() * 0.5) * 0.5
            self.tilt_roll += hover_osc * 0.1
            self.tilt_pitch += math.cos(time.time() * 0.7) * 0.1

    # ========================================================
    # BATTERY UPDATE
    # ========================================================
    def _update_battery(self, delta_time):
        if self.state == "LANDED":
            return
            
        horizontal_speed = self.get_horizontal_speed()
        vertical_speed = abs(self.velocity_z)
        
        if horizontal_speed < 0.5 and vertical_speed < 0.5:
            drain_rate = self.battery_drain_hover
        elif horizontal_speed < 15.0:
            drain_rate = self.battery_drain_cruise + (horizontal_speed / 30) * 0.005
        else:
            drain_rate = self.battery_drain_full + (horizontal_speed / 30) * 0.01
            
        drain_rate += vertical_speed * 0.002
        
        temp_factor = 1 + (self.battery_temperature - 25) * 0.01
        drain_rate *= max(0.5, min(2.0, temp_factor))
        
        health_factor = self.battery_health / 100.0
        drain_rate *= (1 + (1 - health_factor) * 0.5)
        
        self.battery -= drain_rate * delta_time
        self._update_battery_temperature(delta_time, drain_rate)
        
        if self.battery < 0.0:
            self.battery = 0.0
            
    def _update_battery_temperature(self, delta_time, drain_rate):
        heat_generation = drain_rate * 2.0
        ambient_temp = 25.0
        cooling = (self.battery_temperature - ambient_temp) * 0.01
        self.battery_temperature += (heat_generation - cooling) * delta_time
        self.battery_temperature = max(15, min(50, self.battery_temperature))

    # ========================================================
    # SPEED CALCULATIONS
    # ========================================================
    def get_horizontal_speed(self):
        return math.sqrt(self.velocity_x ** 2 + self.velocity_y ** 2)

    def get_total_speed(self):
        return math.sqrt(
            self.velocity_x ** 2 +
            self.velocity_y ** 2 +
            self.velocity_z ** 2
        )

    def get_distance_from_home(self):
        return math.sqrt(
            (self.x - self.home_x) ** 2 +
            (self.y - self.home_y) ** 2 +
            (self.z - self.home_z) ** 2
        )

    def get_altitude_percentage(self):
        if self.max_altitude <= 0:
            return 0.0
        percentage = (self.z / self.max_altitude) * 100.0
        return max(0.0, min(percentage, 100.0))

    def get_altitude_warning(self):
        if self.z <= self.ground_level:
            return "GROUND"
        if self.z <= self.low_altitude_threshold:
            return "LOW_ALTITUDE"
        if self.z >= (self.max_altitude * 0.9):
            return "HIGH_ALTITUDE"
        return "NORMAL"

    # ========================================================
    # GET DRONE STATUS - COMPLETE
    # ========================================================
    def get_status(self):
        horizontal_speed = self.get_horizontal_speed()
        total_speed = self.get_total_speed()
        distance_from_home = self.get_distance_from_home()
        altitude_percentage = self.get_altitude_percentage()
        altitude_warning = self.get_altitude_warning()
        geofence_status = self.geofence.check_position(self.x, self.y)
        signal_status = self.get_signal_strength()
        
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
                "in_no_fly_zone": terrain_info["in_no_fly_zone"],
                "obstacles_detected": len(self.detected_obstacles)
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
            "recording": self.recording,
            "sensors": {
                "gps": {
                    "position": {
                        "x": round(self.gps_position[0], 2),
                        "y": round(self.gps_position[1], 2),
                        "z": round(self.gps_position[2], 2)
                    },
                    "fix_quality": round(self.gps.fix_quality, 2)
                },
                "imu": self.imu_data,
                "barometer": {
                    "altitude": round(self.barometer_altitude, 2)
                },
                "magnetometer": {
                    "heading": round(self.magnetometer_heading, 2)
                }
            },
            "vision": {
                "obstacles": self.detected_obstacles,
                "landing_zone": self.detected_landing_zone
            },
            "flight_id": self.flight_id
        }

    # ========================================================
    # EXPORT FUNCTIONS
    # ========================================================
    def export_telemetry_to_json(self, output_path: str):
        """Export recorded telemetry to JSON file"""
        import json
        with open(output_path, 'w') as f:
            json.dump(self.recording_data, f, indent=2)
        print(f"📁 Telemetry exported to {output_path}")
        return output_path

    def get_flight_history(self, limit: int = 100):
        """Get flight history from database"""
        if self.flight_id:
            return self.storage.get_telemetry(self.flight_id, limit)
        return []