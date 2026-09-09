import asyncio
import time
import math
from contextlib import asynccontextmanager
from enum import Enum
from typing import List, Optional

from fastapi import FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from simulator.core.drone import Drone
from simulator.core.flight_controller import FlightController
from simulator.core.mission_controller import MissionController
from simulator.core.signal import SignalSimulator
from simulator.core.replay import MissionRecorder


# ============================================================
# DRONE + FLIGHT CONTROLLER + MISSION CONTROLLER
# ============================================================

drone = Drone()
controller = FlightController(drone)
mission_controller = None
recorder = MissionRecorder()

# Set controller reference for emergency system
drone.set_controller(controller)


# ============================================================
# COMMAND MODELS
# ============================================================

class MovementDirection(str, Enum):
    forward = "forward"
    backward = "backward"
    left = "left"
    right = "right"


class AltitudeCommand(BaseModel):
    altitude: float = Field(..., ge=0, le=120, description="Target altitude in meters")


class SpeedCommand(BaseModel):
    speed: float = Field(..., ge=0, le=30, description="Target horizontal speed in meters per second")


class MovementCommand(BaseModel):
    direction: MovementDirection = Field(..., description="Direction of horizontal movement")


class WaypointModel(BaseModel):
    x: float = Field(..., description="X coordinate in meters")
    y: float = Field(..., description="Y coordinate in meters")
    altitude: float = Field(..., ge=0, le=120, description="Target altitude in meters")


class MissionLoadCommand(BaseModel):
    waypoints: List[WaypointModel] = Field(..., min_length=1, description="List of waypoints for the mission")


class GeofenceCommand(BaseModel):
    radius: float = Field(..., ge=10, le=500, description="Geofence radius in meters")


class SimulationSpeedCommand(BaseModel):
    speed: float = Field(..., ge=0.1, le=10, description="Simulation speed multiplier")


class WindSpeedCommand(BaseModel):
    speed: float = Field(..., ge=0, le=8, description="Wind speed in meters per second")


class WindDirectionCommand(BaseModel):
    direction: float = Field(..., ge=0, le=360, description="Wind direction in degrees")


class TerrainCommand(BaseModel):
    enabled: bool = Field(..., description="Enable or disable terrain awareness")


class EmergencyCommand(BaseModel):
    type: str = Field(..., description="Emergency type to trigger")


# ============================================================
# SIMULATION LOOP
# ============================================================

simulation_speed = 1.0
recording_filename = None

async def simulation_loop():
    global simulation_speed
    loop = asyncio.get_running_loop()
    previous_time = loop.time()
    frame_count = 0

    while True:
        current_time = loop.time()
        delta_time = current_time - previous_time
        previous_time = current_time

        # Apply speed multiplier
        delta_time *= simulation_speed

        # Update mission controller if it exists
        if mission_controller:
            mission_controller.update(delta_time)

        # Update flight controller
        controller.update(delta_time)

        # Update drone physics
        drone.update(delta_time)

        # Record drone data if recording
        if recorder.recording:
            recorder.record_frame(drone.get_status())

        frame_count += 1

        # Run simulation approximately every 100 ms
        await asyncio.sleep(0.1)


# ============================================================
# FASTAPI LIFESPAN
# ============================================================

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Start simulation in background
    simulation_task = asyncio.create_task(simulation_loop())

    print("========================================")
    print(" Autonomous UAV Simulation Started")
    print("========================================")
    print(f" Geofence Radius: {drone.geofence.radius}m")
    print(f" Max Altitude: {drone.max_altitude}m")
    print(f" Max Speed: {drone.max_speed}m/s")
    print(f" Terrain Awareness: {drone.terrain_awareness}")
    print(f" Obstacles: {len(drone.terrain.obstacles)}")
    print(f" No-Fly Zones: {len(drone.terrain.no_fly_zones)}")
    print("========================================")

    yield

    # Stop simulation when API shuts down
    simulation_task.cancel()
    try:
        await simulation_task
    except asyncio.CancelledError:
        pass

    print("========================================")
    print(" Autonomous UAV Simulation Stopped")
    print("========================================")


# ============================================================
# FASTAPI APPLICATION
# ============================================================

app = FastAPI(
    title="Autonomous UAV Ground Control API",
    description="Ground Control API for the Autonomous UAV simulation system.",
    version="3.0.0",
    lifespan=lifespan
)


# ============================================================
# CORS
# ============================================================

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ============================================================
# ROOT
# ============================================================

@app.get("/")
def root():
    return {
        "message": "Autonomous UAV API is running",
        "status": "online",
        "version": "3.0.0",
        "features": {
            "terrain_awareness": drone.terrain_awareness,
            "wind_simulation": True,
            "signal_simulation": True,
            "emergency_system": True,
            "mission_recording": True
        }
    }


# ============================================================
# HEALTH CHECK
# ============================================================

@app.get("/api/health")
def health_check():
    return {
        "status": "healthy",
        "service": "Autonomous UAV API",
        "drone_state": drone.state,
        "battery": drone.battery,
        "signal_strength": drone.get_signal_strength()["strength"],
        "emergency_active": drone.emergency_active
    }


# ============================================================
# DRONE STATUS
# ============================================================

@app.get("/api/drone/status")
def get_drone_status():
    status = drone.get_status()

    # Home position
    status["home_position"] = {
        "x": drone.home_x,
        "y": drone.home_y,
        "z": drone.home_z
    }

    # Target values
    status["targets"] = {
        "altitude": round(controller.target_altitude, 2),
        "speed": round(controller.target_speed, 2),
        "velocity_x": round(controller.target_velocity_x, 2),
        "velocity_y": round(controller.target_velocity_y, 2)
    }

    # Navigation
    status["navigation"] = {
        "mode": controller.navigation_mode,
        "target_x": controller.target_x,
        "target_y": controller.target_y
    }

    # Mission info
    if mission_controller:
        status["mission"] = mission_controller.get_status()
    else:
        status["mission"] = {
            "status": "IDLE",
            "current_waypoint_index": 0,
            "total_waypoints": 0,
            "progress": 0,
            "current_waypoint": None
        }

    return status


# ============================================================
# DRONE COMMANDS
# ============================================================

@app.post("/api/drone/takeoff")
def takeoff():
    if drone.state != "LANDED":
        return {
            "success": False,
            "message": f"Cannot take off while drone is {drone.state}",
            "status": drone.get_status()
        }

    drone.takeoff()
    controller.start_takeoff()
    if controller.target_altitude <= 0:
        controller.set_altitude(10)

    return {
        "success": True,
        "command": "TAKEOFF",
        "message": "Takeoff command accepted",
        "status": drone.get_status()
    }


@app.post("/api/drone/land")
def land():
    if drone.state not in ["FLYING", "TAKING_OFF"]:
        return {
            "success": False,
            "message": f"Cannot land while drone is {drone.state}",
            "status": drone.get_status()
        }

    drone.land()
    controller.start_landing()

    return {
        "success": True,
        "command": "LAND",
        "message": "Landing command accepted",
        "status": drone.get_status()
    }


@app.post("/api/drone/return-home")
def return_home():
    if drone.state != "FLYING":
        return {
            "success": False,
            "message": "Return Home requires the drone to be flying",
            "status": drone.get_status()
        }

    controller.return_home()

    return {
        "success": True,
        "command": "RETURN_HOME",
        "message": "Return Home navigation activated",
        "home_position": {
            "x": drone.home_x,
            "y": drone.home_y,
            "z": drone.home_z
        },
        "status": drone.get_status()
    }


@app.post("/api/drone/emergency-stop")
def emergency_stop():
    controller.stop_horizontal()
    drone.velocity_x = 0.0
    drone.velocity_y = 0.0
    drone.velocity_z = 0.0
    controller.navigation_mode = "HOLD"
    drone.emergency_active = False

    return {
        "success": True,
        "command": "EMERGENCY_STOP",
        "message": "Emergency stop activated. All commanded movement has been stopped.",
        "status": drone.get_status()
    }


@app.post("/api/drone/altitude")
def set_altitude(command: AltitudeCommand):
    if drone.state == "LANDED" and command.altitude > 0:
        return {
            "success": False,
            "message": "Drone must take off before setting a positive altitude",
            "status": drone.get_status()
        }

    controller.set_altitude(command.altitude)

    return {
        "success": True,
        "command": "SET_ALTITUDE",
        "target_altitude": controller.target_altitude,
        "status": drone.get_status()
    }


@app.post("/api/drone/speed")
def set_speed(command: SpeedCommand):
    controller.set_speed(command.speed)

    return {
        "success": True,
        "command": "SET_SPEED",
        "target_speed": controller.target_speed,
        "status": drone.get_status()
    }


@app.post("/api/drone/speed/increase")
def increase_speed():
    if drone.state != "FLYING":
        return {
            "success": False,
            "message": f"Speed control unavailable while drone is {drone.state}",
            "status": drone.get_status()
        }

    controller.increase_speed()

    return {
        "success": True,
        "command": "INCREASE_SPEED",
        "message": f"Target speed increased to {controller.target_speed:.1f} m/s",
        "target_speed": controller.target_speed,
        "status": drone.get_status()
    }


@app.post("/api/drone/speed/decrease")
def decrease_speed():
    if drone.state != "FLYING":
        return {
            "success": False,
            "message": f"Speed control unavailable while drone is {drone.state}",
            "status": drone.get_status()
        }

    controller.decrease_speed()

    return {
        "success": True,
        "command": "DECREASE_SPEED",
        "message": f"Target speed decreased to {controller.target_speed:.1f} m/s",
        "target_speed": controller.target_speed,
        "status": drone.get_status()
    }


@app.post("/api/drone/move")
def move(command: MovementCommand):
    if drone.state not in ["FLYING", "TAKING_OFF"]:
        return {
            "success": False,
            "message": "Drone is not flying",
            "status": drone.get_status()
        }

    if command.direction == MovementDirection.forward:
        controller.move_forward()
    elif command.direction == MovementDirection.backward:
        controller.move_backward()
    elif command.direction == MovementDirection.left:
        controller.move_left()
    elif command.direction == MovementDirection.right:
        controller.move_right()

    return {
        "success": True,
        "command": "MOVE",
        "direction": command.direction,
        "status": drone.get_status()
    }


@app.post("/api/drone/stop")
def stop_movement():
    controller.stop_horizontal()
    controller.navigation_mode = "HOLD"

    return {
        "success": True,
        "command": "STOP",
        "message": "Horizontal movement stopped",
        "status": drone.get_status()
    }


# ============================================================
# WIND ENDPOINTS
# ============================================================

@app.get("/api/drone/wind")
def get_wind_status():
    """Get current wind conditions"""
    import time
    wind_x, wind_y = drone.wind.get_wind_vector(time.time(), drone.z)
    wind_total = math.sqrt(wind_x**2 + wind_y**2)
    
    return {
        "speed_x": round(wind_x, 2),
        "speed_y": round(wind_y, 2),
        "speed_total": round(wind_total, 2),
        "direction": drone.wind.direction,
        "description": drone.wind.get_wind_description(),
        "gust_strength": drone.wind.gust_strength,
        "base_speed": drone.wind.base_speed
    }


@app.post("/api/drone/wind")
def set_wind_speed(command: WindSpeedCommand):
    """Set wind speed"""
    drone.wind.base_speed = max(0, min(8, command.speed))
    return {
        "success": True,
        "wind_speed": drone.wind.base_speed,
        "message": f"Wind speed set to {drone.wind.base_speed} m/s"
    }


@app.post("/api/drone/wind/direction")
def set_wind_direction(command: WindDirectionCommand):
    """Set wind direction in degrees"""
    drone.wind.direction = command.direction % 360
    return {
        "success": True,
        "wind_direction": drone.wind.direction,
        "message": f"Wind direction set to {drone.wind.direction}°"
    }


# ============================================================
# TERRAIN ENDPOINTS
# ============================================================

@app.get("/api/terrain/info")
def get_terrain_info(x: float = Query(0), y: float = Query(0)):
    """Get terrain information at specified coordinates"""
    terrain_info = drone.terrain.get_terrain_info(x, y)
    
    return {
        "position": {"x": x, "y": y},
        "ground_height": terrain_info["height"],
        "has_obstacle": terrain_info["has_obstacle"],
        "obstacle": terrain_info["obstacle"],
        "in_no_fly_zone": terrain_info["in_no_fly_zone"],
        "no_fly_zone": terrain_info["no_fly_zone"]
    }


@app.get("/api/terrain/obstacles")
def get_obstacles():
    """Get all obstacles"""
    return {
        "obstacles": drone.terrain.obstacles,
        "count": len(drone.terrain.obstacles)
    }


@app.get("/api/terrain/no-fly-zones")
def get_no_fly_zones():
    """Get all no-fly zones"""
    return {
        "no_fly_zones": drone.terrain.no_fly_zones,
        "count": len(drone.terrain.no_fly_zones)
    }


@app.post("/api/terrain/awareness")
def set_terrain_awareness(command: TerrainCommand):
    """Enable or disable terrain awareness"""
    drone.terrain_awareness = command.enabled
    return {
        "success": True,
        "terrain_awareness": drone.terrain_awareness,
        "message": f"Terrain awareness {'enabled' if command.enabled else 'disabled'}"
    }


# ============================================================
# SIGNAL ENDPOINTS
# ============================================================

@app.get("/api/signal/status")
def get_signal_status():
    """Get current signal status"""
    signal_data = drone.get_signal_strength()
    
    return {
        "strength": signal_data["strength"],
        "quality": signal_data["quality"],
        "latency": signal_data["latency"],
        "distance": signal_data["distance"],
        "signal_lost": signal_data["strength"] < 0.1
    }


@app.post("/api/signal/interference")
def add_interference_zone(x: float, y: float, radius: float, strength: float = 0.3):
    """Add an interference zone"""
    drone.signal.add_interference_zone(x, y, radius, strength)
    return {
        "success": True,
        "message": f"Interference zone added at ({x}, {y}) with radius {radius}m",
        "interference_zones": len(drone.signal.interference_zones)
    }


# ============================================================
# EMERGENCY ENDPOINTS
# ============================================================

@app.get("/api/emergency/status")
def get_emergency_status():
    """Get current emergency status"""
    return {
        "active": drone.emergency_active,
        "type": drone.emergency_type if drone.emergency_active else None,
        "timer": drone.emergency.emergency_timer if drone.emergency_active else 0
    }


@app.post("/api/emergency/trigger")
def trigger_emergency(command: EmergencyCommand):
    """Manually trigger an emergency"""
    if command.type not in drone.emergency.failure_modes:
        return {
            "success": False,
            "message": f"Unknown emergency type: {command.type}",
            "available_types": list(drone.emergency.failure_modes.keys())
        }
    
    result = drone.emergency.trigger_emergency(command.type)
    if result:
        drone.emergency_active = True
        drone.emergency_type = command.type
        return {
            "success": True,
            "message": f"Emergency triggered: {result['message']}",
            "emergency": result
        }
    
    return {
        "success": False,
        "message": "Failed to trigger emergency"
    }


@app.post("/api/emergency/resolve")
def resolve_emergency():
    """Resolve the current emergency"""
    drone.emergency.resolve_emergency()
    drone.emergency_active = False
    drone.emergency_type = None
    return {
        "success": True,
        "message": "Emergency resolved"
    }


# ============================================================
# MISSION ENDPOINTS
# ============================================================

@app.post("/api/mission/load")
def load_mission(command: MissionLoadCommand):
    global mission_controller

    # Create or reset mission controller
    mission_controller = MissionController(drone, controller)
    success, message = mission_controller.load_mission([w.dict() for w in command.waypoints])

    return {
        "success": success,
        "message": message,
        "waypoints": command.waypoints,
        "status": drone.get_status()
    }


@app.post("/api/mission/start")
def start_mission():
    if not mission_controller:
        return {"success": False, "message": "No mission loaded"}

    success, message = mission_controller.start_mission()

    return {
        "success": success,
        "message": message,
        "status": drone.get_status()
    }


@app.post("/api/mission/pause")
def pause_mission():
    if not mission_controller:
        return {"success": False, "message": "No mission loaded"}

    success, message = mission_controller.pause_mission()

    return {
        "success": success,
        "message": message,
        "status": drone.get_status()
    }


@app.post("/api/mission/resume")
def resume_mission():
    if not mission_controller:
        return {"success": False, "message": "No mission loaded"}

    success, message = mission_controller.resume_mission()

    return {
        "success": success,
        "message": message,
        "status": drone.get_status()
    }


@app.post("/api/mission/abort")
def abort_mission():
    if not mission_controller:
        return {"success": False, "message": "No mission loaded"}

    success, message = mission_controller.abort_mission()

    return {
        "success": success,
        "message": message,
        "status": drone.get_status()
    }


@app.post("/api/mission/reset")
def reset_mission():
    global mission_controller

    if mission_controller:
        mission_controller.reset_mission()
        mission_controller = None

    return {
        "success": True,
        "message": "Mission reset",
        "status": drone.get_status()
    }


@app.get("/api/mission/status")
def get_mission_status():
    if not mission_controller:
        return {
            "status": "IDLE",
            "current_waypoint_index": 0,
            "total_waypoints": 0,
            "progress": 0,
            "current_waypoint": None
        }

    return mission_controller.get_status()


# ============================================================
# GEOFENCE ENDPOINTS
# ============================================================

@app.post("/api/geofence/set")
def set_geofence(command: GeofenceCommand):
    drone.geofence.radius = command.radius

    return {
        "success": True,
        "radius": command.radius,
        "center_x": drone.geofence.center_x,
        "center_y": drone.geofence.center_y,
        "message": f"Geofence radius set to {command.radius}m"
    }


@app.get("/api/geofence/status")
def get_geofence_status():
    status = drone.geofence.check_position(drone.x, drone.y)

    return {
        "center_x": drone.geofence.center_x,
        "center_y": drone.geofence.center_y,
        "radius": drone.geofence.radius,
        "distance_from_center": status["distance"],
        "is_breached": status["is_breached"],
        "is_warning": status["is_warning"],
        "distance_percentage": status["distance_percentage"]
    }


# ============================================================
# SIMULATION SPEED
# ============================================================

@app.post("/api/simulation/speed")
def set_simulation_speed(command: SimulationSpeedCommand):
    global simulation_speed
    simulation_speed = command.speed

    return {
        "success": True,
        "speed": simulation_speed,
        "message": f"Simulation speed set to {simulation_speed}x"
    }


@app.get("/api/simulation/speed")
def get_simulation_speed():
    return {
        "speed": simulation_speed,
        "is_running": True
    }


# ============================================================
# MISSION RECORDING & REPLAY
# ============================================================

@app.post("/api/replay/start")
def start_recording():
    """Start recording mission data"""
    if recorder.start_recording():
        drone.recording = True
        return {
            "success": True,
            "message": "Recording started",
            "recording": True
        }
    return {
        "success": False,
        "message": "Failed to start recording"
    }


@app.post("/api/replay/stop")
def stop_recording():
    """Stop recording and save"""
    global recording_filename
    filename = recorder.stop_recording()
    drone.recording = False
    
    if filename:
        recording_filename = filename
        return {
            "success": True,
            "message": f"Recording saved to {filename}",
            "filename": filename,
            "frames": len(recorder.recording_data)
        }
    return {
        "success": False,
        "message": "No data recorded"
    }


@app.get("/api/replay/list")
def list_recordings():
    """List available recordings"""
    import os
    recordings = []
    for file in os.listdir('.'):
        if file.startswith('mission_') and file.endswith('.json'):
            size = os.path.getsize(file)
            recordings.append({
                "name": file,
                "size": size,
                "size_kb": round(size / 1024, 2)
            })
    return {"recordings": recordings}


@app.post("/api/replay/load")
def load_recording(filename: str):
    """Load a recording for playback"""
    if recorder.load_recording(filename):
        return {
            "success": True,
            "message": f"Loaded {filename}",
            "frames": len(recorder.playback_data)
        }
    return {
        "success": False,
        "message": "Failed to load recording"
    }


@app.post("/api/replay/play")
def start_playback():
    """Start mission playback"""
    if recorder.start_playback():
        return {
            "success": True,
            "message": "Playback started"
        }
    return {
        "success": False,
        "message": "No recording loaded"
    }


@app.post("/api/replay/stop")
def stop_playback():
    """Stop mission playback"""
    recorder.stop_playback()
    return {
        "success": True,
        "message": "Playback stopped"
    }


@app.get("/api/replay/status")
def get_replay_status():
    """Get playback status"""
    return {
        "playing": recorder.playback,
        "progress": recorder.get_playback_progress(),
        "recording": recorder.recording,
        "frames": len(recorder.playback_data) if recorder.playback_data else 0,
        "current_frame": recorder.playback_index if recorder.playback else 0
    }


@app.get("/api/replay/frame")
def get_replay_frame():
    """Get the next frame during playback"""
    if not recorder.playback:
        return {"playing": False}
    
    frame = recorder.get_next_frame()
    if frame:
        return {
            "playing": True,
            "frame": frame,
            "progress": recorder.get_playback_progress()
        }
    else:
        recorder.stop_playback()
        return {
            "playing": False,
            "complete": True,
            "message": "Playback complete"
        }
    # Add these endpoints to main.py

@app.get("/api/sensors/status")
def get_sensor_status():
    """Get simulated sensor readings"""
    return {
        "gps": {
            "position": (drone.x, drone.y, drone.z),
            "fix_quality": drone.gps.fix_quality
        },
        "imu": drone.imu.update(
            (drone.acceleration_x, drone.acceleration_y, drone.acceleration_z),
            (0, 0, 0)  # gyro readings
        ),
        "barometer": {
            "altitude": drone.barometer.update(drone.z)
        },
        "magnetometer": {
            "heading": drone.magnetometer.update(0)
        }
    }

@app.post("/api/simulation/record")
def start_recording():
    """Start recording telemetry data to database"""
    drone.flight_id = datetime.now().strftime("%Y%m%d_%H%M%S")
    return {
        "success": True,
        "flight_id": drone.flight_id,
        "message": f"Recording started for flight {drone.flight_id}"
    }

@app.post("/api/simulation/stop-recording")
def stop_recording():
    """Stop recording and save flight summary"""
    if not drone.flight_id:
        return {"success": False, "message": "No active recording"}
    
    # Save flight summary
    summary = {
        "start_time": drone.flight_start_time or 0,
        "end_time": time.time(),
        "duration": drone.total_flight_time,
        "distance": drone.distance_travelled,
        "max_altitude": max(drone.z, 0),
        "max_speed": drone.max_speed,
        "avg_battery": 80,  # placeholder
        "waypoints": 0,  # placeholder
        "status": drone.state
    }
    drone.storage.save_flight_summary(drone.flight_id, summary)
    
    flight_id = drone.flight_id
    drone.flight_id = None
    
    return {
        "success": True,
        "flight_id": flight_id,
        "message": f"Recording stopped for flight {flight_id}"
    }

@app.get("/api/data/flights")
def get_flights():
    """Get list of all recorded flights"""
    return {"flights": drone.storage.get_flights()}

@app.get("/api/data/telemetry")
def get_telemetry(flight_id: str, limit: int = 1000):
    """Get telemetry data for a specific flight"""
    return {"telemetry": drone.storage.get_telemetry(flight_id, limit)}

@app.post("/api/simulation/emergency-land")
def emergency_land():
    """Emergency landing procedure"""
    drone.emergency.trigger_emergency("emergency_land")
    return {
        "success": True,
        "message": "Emergency landing initiated"
    }