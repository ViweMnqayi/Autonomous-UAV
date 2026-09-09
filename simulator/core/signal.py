import math
import random


class SignalSimulator:
    """Simulates RF signal strength between drone and ground station"""
    
    def __init__(self, max_range=500.0, base_strength=1.0):
        self.max_range = max_range  # meters
        self.base_strength = base_strength
        self.noise_level = 0.05
        self.interference_zones = []
        self.signal_quality = 1.0
        self.latency = 0.05  # seconds
        
    def add_interference_zone(self, x, y, radius, strength=0.3):
        """Add an area with signal interference"""
        self.interference_zones.append({
            "x": x,
            "y": y,
            "radius": radius,
            "strength": strength
        })
        
    def get_signal_strength(self, drone_x, drone_y, drone_z, base_x=0, base_y=0):
        """Calculate signal strength based on distance and interference"""
        # Distance from base station
        distance = math.sqrt(
            (drone_x - base_x)**2 + 
            (drone_y - base_y)**2 + 
            (drone_z)**2  # Altitude affects signal too
        )
        
        # Base signal strength (inverse square law)
        if distance < self.max_range:
            strength = 1 - (distance / self.max_range)
        else:
            strength = 0
            
        # Add altitude factor (signal degrades with altitude)
        altitude_factor = 1 - (drone_z / 200) * 0.3
        strength *= max(0.1, altitude_factor)
        
        # Check interference zones
        for zone in self.interference_zones:
            zone_distance = math.sqrt(
                (drone_x - zone["x"])**2 + 
                (drone_y - zone["y"])**2
            )
            
            if zone_distance < zone["radius"]:
                interference = 1 - (zone_distance / zone["radius"])
                strength *= (1 - interference * zone["strength"])
        
        # Add noise
        noise = random.uniform(-self.noise_level, self.noise_level)
        strength = max(0, min(1, strength + noise))
        
        # Update signal quality
        self.signal_quality = strength
        
        # Update latency based on signal quality
        self.latency = 0.02 + (1 - strength) * 0.08
        
        return {
            "strength": round(strength, 3),
            "quality": self._get_quality_label(strength),
            "latency": round(self.latency * 1000, 1),  # ms
            "distance": round(distance, 1)
        }
    
    def _get_quality_label(self, strength):
        if strength > 0.8:
            return "Excellent"
        elif strength > 0.6:
            return "Good"
        elif strength > 0.4:
            return "Fair"
        elif strength > 0.2:
            return "Poor"
        else:
            return "Critical"