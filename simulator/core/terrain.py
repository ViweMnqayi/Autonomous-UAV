import math
import random
import noise  # Install: pip install noise


class TerrainGenerator:
    """Generates realistic terrain with hills, valleys, and obstacles"""
    
    def __init__(self, width=200, height=200, seed=None):
        self.width = width
        self.height = height
        self.seed = seed or random.randint(0, 1000)
        self.height_map = None
        self.obstacles = []
        self.no_fly_zones = []
        
    def generate_height_map(self):
        """Generate terrain height map using Perlin noise"""
        self.height_map = []
        
        for y in range(self.height):
            row = []
            for x in range(self.width):
                # Normalize coordinates
                nx = x / self.width - 0.5
                ny = y / self.height - 0.5
                
                # Perlin noise for terrain
                elevation = noise.pnoise2(
                    nx * 2 + self.seed,
                    ny * 2 + self.seed,
                    octaves=6,
                    persistence=0.5,
                    lacunarity=2.0
                )
                
                # Add some variation
                elevation += noise.pnoise2(
                    nx * 4 + self.seed * 2,
                    ny * 4 + self.seed * 2,
                    octaves=3,
                    persistence=0.3,
                    lacunarity=2.5
                ) * 0.3
                
                # Scale to reasonable heights
                elevation = (elevation + 1) * 15  # 0-30m height
                elevation = max(0, min(30, elevation))
                
                row.append(elevation)
            self.height_map.append(row)
            
        return self.height_map
    
    def generate_obstacles(self, count=15):
        """Generate random obstacles (buildings, trees, etc.)"""
        self.obstacles = []
        
        for _ in range(count):
            obstacle = {
                "x": random.uniform(-90, 90),
                "y": random.uniform(-90, 90),
                "height": random.uniform(3, 25),
                "width": random.uniform(2, 8),
                "type": random.choice(["tree", "building", "tower", "antenna"]),
                "id": len(self.obstacles) + 1
            }
            
            # Check if obstacle is too close to home
            distance = math.sqrt(obstacle["x"]**2 + obstacle["y"]**2)
            if distance < 10:
                continue
                
            self.obstacles.append(obstacle)
            
        return self.obstacles
    
    def generate_no_fly_zones(self, count=3):
        """Generate no-fly zones (restricted areas)"""
        self.no_fly_zones = []
        
        for _ in range(count):
            zone = {
                "x": random.uniform(-60, 60),
                "y": random.uniform(-60, 60),
                "radius": random.uniform(10, 30),
                "type": random.choice(["airport", "military", "restricted"]),
                "id": len(self.no_fly_zones) + 1
            }
            
            # Check if zone is too close to home
            distance = math.sqrt(zone["x"]**2 + zone["y"]**2)
            if distance < 20:
                continue
                
            self.no_fly_zones.append(zone)
            
        return self.no_fly_zones
    
    def get_height_at(self, x, y):
        """Get terrain height at specific coordinates"""
        if not self.height_map:
            self.generate_height_map()
            
        # Convert world coordinates to map indices
        map_x = int((x / 100 + 0.5) * self.width)
        map_y = int((y / 100 + 0.5) * self.height)
        
        # Clamp to map boundaries
        map_x = max(0, min(self.width - 1, map_x))
        map_y = max(0, min(self.height - 1, map_y))
        
        return self.height_map[map_y][map_x]
    
    def check_obstacle_collision(self, x, y, z, radius=1.5):
        """Check if drone is colliding with any obstacle"""
        for obstacle in self.obstacles:
            distance = math.sqrt(
                (x - obstacle["x"])**2 + 
                (y - obstacle["y"])**2
            )
            
            if distance < (obstacle["width"] / 2 + radius):
                if z < obstacle["height"]:
                    return True, obstacle
                    
        return False, None
    
    def check_no_fly_zone(self, x, y):
        """Check if position is inside a no-fly zone"""
        for zone in self.no_fly_zones:
            distance = math.sqrt(
                (x - zone["x"])**2 + 
                (y - zone["y"])**2
            )
            
            if distance < zone["radius"]:
                return True, zone
                
        return False, None
    
    def get_terrain_info(self, x, y):
        """Get complete terrain information at position"""
        height = self.get_height_at(x, y)
        has_obstacle, obstacle = self.check_obstacle_collision(x, y, height)
        in_no_fly, zone = self.check_no_fly_zone(x, y)
        
        return {
            "height": round(height, 2),
            "has_obstacle": has_obstacle,
            "obstacle": obstacle,
            "in_no_fly_zone": in_no_fly,
            "no_fly_zone": zone
        }