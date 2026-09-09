"""
Core simulation modules for the Autonomous UAV system.
"""

from simulator.core.drone import Drone
from simulator.core.flight_controller import FlightController
from simulator.core.mission_controller import MissionController
from simulator.core.wind import WindSystem
from simulator.core.terrain import TerrainGenerator
from simulator.core.signal import SignalSimulator
from simulator.core.physics import PhysicsEngine
from simulator.core.pid import PID, AltitudeController, VelocityController
from simulator.core.sensors import GPS, IMU, Barometer, Magnetometer
from simulator.core.emergency import EmergencySystem
from simulator.core.geofence import Geofence  # Add this
from simulator.core.vision import VisionSystem
from simulator.core.data_storage import TelemetryStorage
from simulator.core.replay import MissionRecorder

__all__ = [
    'Drone',
    'FlightController',
    'MissionController',
    'WindSystem',
    'TerrainGenerator',
    'SignalSimulator',
    'PhysicsEngine',
    'PID',
    'AltitudeController',
    'VelocityController',
    'GPS',
    'IMU',
    'Barometer',
    'Magnetometer',
    'EmergencySystem',
    'Geofence',
    'VisionSystem',
    'TelemetryStorage',
    'MissionRecorder',
]

__version__ = '1.0.0'