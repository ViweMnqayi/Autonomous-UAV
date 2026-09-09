import random
import math


class EmergencySystem:
    """Handles emergency situations and automated responses"""
    
    def __init__(self, drone, controller):
        self.drone = drone
        self.controller = controller
        self.emergency_type = None
        self.emergency_active = False
        self.emergency_timer = 0
        
        # Failure modes
        self.failure_modes = {
            "motor_failure": {
                "probability": 0.001,
                "message": "Motor failure detected!",
                "action": "auto_land"
            },
            "gps_loss": {
                "probability": 0.002,
                "message": "GPS signal lost! Switching to altitude hold.",
                "action": "hold_position"
            },
            "compass_error": {
                "probability": 0.0015,
                "message": "Compass error detected!",
                "action": "emergency_land"
            },
            "battery_critical": {
                "probability": 0.005,
                "message": "Battery critically low!",
                "action": "auto_land"
            },
            "signal_loss": {
                "probability": 0.003,
                "message": "Signal lost! Returning home.",
                "action": "return_home"
            }
        }
        
    def check_emergencies(self, delta_time):
        """Check for emergency conditions"""
        if self.emergency_active:
            self.emergency_timer += delta_time
            return
            
        # Check battery critical
        if self.drone.battery < 10:
            self.trigger_emergency("battery_critical")
            return
            
        # Check altitude warning
        if self.drone.get_altitude_warning() in ["LOW_ALTITUDE", "GROUND"]:
            if self.drone.velocity_z < -3:  # Fast descent
                self.trigger_emergency("motor_failure")
                return
                
        # Random failures (only when flying)
        if self.drone.state == "FLYING":
            for failure_mode, config in self.failure_modes.items():
                if random.random() < config["probability"] * delta_time:
                    self.trigger_emergency(failure_mode)
                    return
                    
    def trigger_emergency(self, failure_type):
        """Trigger an emergency situation"""
        if failure_type not in self.failure_modes:
            return
            
        self.emergency_active = True
        self.emergency_type = failure_type
        config = self.failure_modes[failure_type]
        
        # Execute emergency action
        action = config["action"]
        if action == "auto_land":
            self.drone.land()
            self.controller.start_landing()
        elif action == "hold_position":
            self.controller.hold_position()
        elif action == "emergency_land":
            self.drone.land()
            self.controller.emergency_stop()
        elif action == "return_home":
            self.controller.return_home()
            
        return {
            "type": failure_type,
            "message": config["message"],
            "action": action
        }
        
    def resolve_emergency(self):
        """Resolve the current emergency"""
        self.emergency_active = False
        self.emergency_type = None
        self.emergency_timer = 0