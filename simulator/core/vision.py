import random
import math


class VisionSystem:
    """Simulated computer vision system for obstacle detection"""
    
    def __init__(self, detection_range=50.0, field_of_view=60):
        self.detection_range = detection_range
        self.field_of_view = field_of_view
        self.detection_accuracy = 0.85
        
    def detect_obstacles(self, drone_x: float, drone_y: float, drone_z: float,
                         heading: float, terrain_obstacles: list) -> list:
        """Detect obstacles within range and field of view"""
        detected = []
        
        for obstacle in terrain_obstacles:
            # Calculate distance to obstacle
            dx = obstacle['x'] - drone_x
            dy = obstacle['y'] - drone_y
            distance = math.sqrt(dx**2 + dy**2)
            
            if distance > self.detection_range:
                continue
            
            # Check if within field of view
            angle_to_obstacle = math.degrees(math.atan2(dy, dx))
            angle_diff = abs(angle_to_obstacle - heading)
            
            if angle_diff > self.field_of_view / 2:
                continue
            
            # Simulate detection accuracy
            if random.random() > self.detection_accuracy:
                continue
            
            # Calculate obstacle size (perspective)
            size = 1 / (distance + 1) * 100
            
            detected.append({
                'x': obstacle['x'],
                'y': obstacle['y'],
                'height': obstacle['height'],
                'width': obstacle['width'],
                'type': obstacle['type'],
                'distance': distance,
                'angle': angle_to_obstacle,
                'size': size
            })
        
        return detected
    
    def detect_landing_zone(self, terrain: list, drone_x: float, drone_y: float) -> dict:
        """Find a safe landing zone"""
        # Simple algorithm: find flat area with no obstacles
        candidates = []
        
        for x in range(-50, 50, 10):
            for y in range(-50, 50, 10):
                terrain_height = terrain.get_height_at(x, y) if terrain else 0
                has_obstacle = terrain.check_obstacle_collision(x, y, 0) if terrain else False
                
                if not has_obstacle and terrain_height < 2:
                    candidates.append({
                        'x': x,
                        'y': y,
                        'height': terrain_height,
                        'distance': math.sqrt((x - drone_x)**2 + (y - drone_y)**2)
                    })
        
        if not candidates:
            return None
        
        # Pick closest candidate
        candidates.sort(key=lambda c: c['distance'])
        return candidates[0]