import math


class MissionController:
    def __init__(self, drone, flight_controller):
        self.drone = drone
        self.flight_controller = flight_controller
        self.waypoints = []
        self.current_waypoint_index = 0
        self.mission_status = "IDLE"  # IDLE, LOADED, ACTIVE, PAUSED, COMPLETED, ABORTED
        self.arrival_threshold = 3.0  # meters
        
    def load_mission(self, waypoints):
        """Load a list of waypoints for the mission"""
        self.waypoints = waypoints
        self.current_waypoint_index = 0
        self.mission_status = "LOADED"
        return True, f"Loaded {len(waypoints)} waypoints"
        
    def start_mission(self):
        """Start executing the loaded mission"""
        if not self.waypoints:
            return False, "No waypoints loaded"
        if self.drone.state != "FLYING":
            return False, "Drone must be flying to start mission"
        if self.mission_status == "COMPLETED":
            return False, "Mission already completed"
            
        self.mission_status = "ACTIVE"
        self._navigate_to_waypoint(self.current_waypoint_index)
        return True, "Mission started"
        
    def pause_mission(self):
        """Pause the current mission"""
        if self.mission_status != "ACTIVE":
            return False, "No active mission to pause"
        self.mission_status = "PAUSED"
        self.flight_controller.stop_horizontal()
        return True, "Mission paused"
        
    def resume_mission(self):
        """Resume a paused mission"""
        if self.mission_status != "PAUSED":
            return False, "Mission is not paused"
        self.mission_status = "ACTIVE"
        self._navigate_to_waypoint(self.current_waypoint_index)
        return True, "Mission resumed"
        
    def abort_mission(self):
        """Abort the current mission and return home"""
        if self.mission_status in ["IDLE", "LOADED", "COMPLETED"]:
            return False, "No active mission to abort"
            
        self.mission_status = "ABORTED"
        self.flight_controller.return_home()
        return True, "Mission aborted, returning home"
        
    def reset_mission(self):
        """Reset mission state"""
        self.waypoints = []
        self.current_waypoint_index = 0
        self.mission_status = "IDLE"
        return True, "Mission reset"
        
    def _navigate_to_waypoint(self, index):
        """Set flight controller target to specific waypoint"""
        if index >= len(self.waypoints):
            self._complete_mission()
            return
            
        waypoint = self.waypoints[index]
        # Set altitude first
        self.flight_controller.set_altitude(waypoint.get("altitude", 10.0))
        # Then set position target
        self.flight_controller.navigate_to(waypoint.get("x", 0.0), waypoint.get("y", 0.0))
        
    def update(self, delta_time):
        """Called every simulation tick to check mission progress"""
        if self.mission_status != "ACTIVE":
            return
            
        if self.current_waypoint_index >= len(self.waypoints):
            self._complete_mission()
            return
            
        # Check if reached current waypoint
        waypoint = self.waypoints[self.current_waypoint_index]
        distance = math.sqrt(
            (self.drone.x - waypoint.get("x", 0.0)) ** 2 +
            (self.drone.y - waypoint.get("y", 0.0)) ** 2
        )
        
        # Also check altitude proximity
        altitude_diff = abs(self.drone.z - waypoint.get("altitude", 10.0))
        
        if distance < self.arrival_threshold and altitude_diff < 2.0:
            # Move to next waypoint
            self.current_waypoint_index += 1
            if self.current_waypoint_index < len(self.waypoints):
                self._navigate_to_waypoint(self.current_waypoint_index)
            else:
                self._complete_mission()
                
    def _complete_mission(self):
        """Mission completed - return home"""
        self.mission_status = "COMPLETED"
        self.flight_controller.return_home()
        
    def get_status(self):
        """Get current mission status"""
        progress = 0
        if self.waypoints:
            progress = (self.current_waypoint_index / len(self.waypoints)) * 100
            progress = min(progress, 100)
            
        current_waypoint = None
        if self.current_waypoint_index < len(self.waypoints):
            current_waypoint = self.waypoints[self.current_waypoint_index]
            
        return {
            "status": self.mission_status,
            "current_waypoint_index": self.current_waypoint_index,
            "total_waypoints": len(self.waypoints),
            "progress": round(progress, 2),
            "current_waypoint": current_waypoint
        }