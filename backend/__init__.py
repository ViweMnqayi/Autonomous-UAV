"""
Autonomous UAV Simulation Package

This package provides a complete UAV simulation framework including:
- Drone physics and dynamics
- Flight control systems
- Mission planning and execution
- Environmental simulation (wind, terrain, signal)
- Sensor simulation (GPS, IMU, Barometer, Magnetometer)
- Emergency handling
- Vision systems
- Data storage and replay
- Machine learning integration
"""

# Core simulation modules
from simulator.core.drone import Drone
from simulator.core.flight_controller import FlightController
from simulator.core.mission_controller import MissionController

# Environmental simulation
from simulator.core.wind import WindSystem
from simulator.core.terrain import TerrainGenerator
from simulator.core.signal import SignalSimulator

# Physics and dynamics
from simulator.core.physics import PhysicsEngine
from simulator.core.pid import PID, AltitudeController, VelocityController

# Sensor simulation
from simulator.core.sensors import GPS, IMU, Barometer, Magnetometer

# Emergency and safety
from simulator.core.emergency import EmergencySystem
from simulator.core.geofence import Geofence

# Vision and perception
from simulator.core.vision import VisionSystem

# Data management
from simulator.core.data_storage import TelemetryStorage
from simulator.core.replay import MissionRecorder

# Machine learning
try:
    from simulator.ml.anomaly_detection import AnomalyDetector
except ImportError:
    # ML dependencies not installed
    pass

__all__ = [
    # Core
    'Drone',
    'FlightController',
    'MissionController',
    
    # Environmental
    'WindSystem',
    'TerrainGenerator',
    'SignalSimulator',
    
    # Physics
    'PhysicsEngine',
    'PID',
    'AltitudeController',
    'VelocityController',
    
    # Sensors
    'GPS',
    'IMU',
    'Barometer',
    'Magnetometer',
    
    # Emergency
    'EmergencySystem',
    'Geofence',
    
    # Vision
    'VisionSystem',
    
    # Data
    'TelemetryStorage',
    'MissionRecorder',
]

__version__ = '5.0.0'
__author__ = 'Viwe Mnqayi'

# Package metadata
PACKAGE_INFO = {
    'name': 'autonomous-uav',
    'version': __version__,
    'author': __author__,
    'description': 'Autonomous UAV Simulation & Ground Control System',
    'features': {
        'physics': True,
        'wind': True,
        'terrain': True,
        'signal': True,
        'sensors': True,
        'vision': True,
        'emergency': True,
        'mission': True,
        'replay': True,
        'storage': True,
    }
}

def get_package_info():
    """Get package information"""
    return PACKAGE_INFO

def get_version():
    """Get package version"""
    return __version__

# Check for optional dependencies
def check_dependencies():
    """Check if optional dependencies are installed"""
    dependencies = {
        'numpy': False,
        'scikit-learn': False,
        'joblib': False,
        'noise': False,
        'sqlite3': True,  # Built-in
    }
    
    try:
        import numpy
        dependencies['numpy'] = True
    except ImportError:
        pass
    
    try:
        import sklearn
        dependencies['scikit-learn'] = True
    except ImportError:
        pass
    
    try:
        import joblib
        dependencies['joblib'] = True
    except ImportError:
        pass
    
    try:
        import noise
        dependencies['noise'] = True
    except ImportError:
        pass
    
    return dependencies

def print_package_info():
    """Print package information to console"""
    print("=" * 50)
    print("[UAV] {0}".format(PACKAGE_INFO['name']))
    print("[Version] {0}".format(PACKAGE_INFO['version']))
    print("[Author] {0}".format(PACKAGE_INFO['author']))
    print("[Description] {0}".format(PACKAGE_INFO['description']))
    print("-" * 50)
    print("Features:")
    for feature, enabled in PACKAGE_INFO['features'].items():
        status = "[X]" if enabled else "[ ]"
        print("  {0} {1}".format(status, feature.title()))
    print("-" * 50)
    print("Dependencies:")
    for dep, installed in check_dependencies().items():
        status = "[X]" if installed else "[ ]"
        print("  {0} {1}".format(status, dep))
    print("=" * 50)