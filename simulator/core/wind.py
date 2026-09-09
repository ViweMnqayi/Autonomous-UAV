import math
import random


class WindSystem:
    """Realistic wind simulation with gusts and altitude effects"""
    
    def __init__(self):
        self.base_speed = 2.0  # m/s
        self.max_speed = 8.0  # m/s
        self.direction = 45  # degrees (0 = North, 90 = East)
        self.gust_strength = 1.5  # m/s
        self.gust_interval = 3.0  # seconds
        self.turbulence = 0.3  # Random turbulence factor
        
        # Wind variation over time
        self.time_offset = random.uniform(0, 100)
        
    def get_wind_vector(self, time: float, altitude: float) -> tuple:
        """
        Returns wind vector (x, y) in m/s
        Wind speed increases with altitude
        """
        # Altitude factor - wind increases with height
        altitude_factor = 1 + (altitude / 100) * 0.8
        altitude_factor = min(altitude_factor, 2.5)  # Cap at 2.5x
        
        # Gust effect
        gust = math.sin(time / self.gust_interval + self.time_offset) * self.gust_strength
        
        # Turbulence (random variations)
        turbulence = (math.sin(time * 0.7 + self.time_offset) * 0.3 + 
                     math.cos(time * 1.3 + self.time_offset * 2) * 0.2) * self.turbulence
        
        # Calculate total speed
        total_speed = (self.base_speed + gust + turbulence) * altitude_factor
        total_speed = max(0, min(total_speed, self.max_speed))
        
        # Convert direction to vector
        rad = math.radians(self.direction + math.sin(time * 0.01) * 5)  # Direction slowly shifts
        wind_x = total_speed * math.cos(rad)
        wind_y = total_speed * math.sin(rad)
        
        return wind_x, wind_y
    
    def get_wind_description(self) -> str:
        """Get human-readable wind description"""
        if self.base_speed < 1:
            return "Calm"
        elif self.base_speed < 3:
            return "Light breeze"
        elif self.base_speed < 5:
            return "Moderate wind"
        elif self.base_speed < 7:
            return "Strong wind"
        else:
            return "Gale force"