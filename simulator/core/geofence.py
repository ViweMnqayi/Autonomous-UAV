import math


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