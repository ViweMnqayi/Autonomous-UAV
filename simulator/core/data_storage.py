import json
import sqlite3
import os
from datetime import datetime
from typing import List, Dict, Any, Optional


class TelemetryStorage:
    """Persistent storage for telemetry data using SQLite"""
    
    def __init__(self, db_path: str = "telemetry.db"):
        self.db_path = db_path
        self._init_database()
        
    def _init_database(self):
        """Initialize SQLite database with required tables"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Create telemetry table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS telemetry (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp REAL,
                flight_id TEXT,
                state TEXT,
                position_x REAL,
                position_y REAL,
                position_z REAL,
                velocity_x REAL,
                velocity_y REAL,
                velocity_z REAL,
                acceleration_x REAL,
                acceleration_y REAL,
                acceleration_z REAL,
                speed_horizontal REAL,
                speed_total REAL,
                altitude REAL,
                battery REAL,
                battery_temperature REAL,
                battery_health REAL,
                flight_time REAL,
                distance_travelled REAL,
                distance_from_home REAL,
                wind_speed_x REAL,
                wind_speed_y REAL,
                signal_strength REAL,
                signal_quality TEXT,
                mission_status TEXT,
                waypoint_index INTEGER,
                emergency_active INTEGER
            )
        ''')
        
        # Create flights table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS flights (
                id TEXT PRIMARY KEY,
                start_time REAL,
                end_time REAL,
                duration REAL,
                distance REAL,
                max_altitude REAL,
                max_speed REAL,
                avg_battery REAL,
                waypoints INTEGER,
                status TEXT
            )
        ''')
        
        conn.commit()
        conn.close()
        
    def save_telemetry(self, data: Dict[str, Any], flight_id: Optional[str] = None) -> None:
        """Save a telemetry data point"""
        if flight_id is None:
            flight_id = datetime.now().strftime("%Y%m%d_%H%M%S")
            
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO telemetry (
                timestamp, flight_id, state,
                position_x, position_y, position_z,
                velocity_x, velocity_y, velocity_z,
                acceleration_x, acceleration_y, acceleration_z,
                speed_horizontal, speed_total,
                altitude, battery, battery_temperature, battery_health,
                flight_time, distance_travelled, distance_from_home,
                wind_speed_x, wind_speed_y,
                signal_strength, signal_quality,
                mission_status, waypoint_index, emergency_active
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            data.get('timestamp', 0),
            flight_id,
            data.get('state', ''),
            data.get('position', {}).get('x', 0),
            data.get('position', {}).get('y', 0),
            data.get('position', {}).get('z', 0),
            data.get('velocity', {}).get('x', 0),
            data.get('velocity', {}).get('y', 0),
            data.get('velocity', {}).get('z', 0),
            data.get('acceleration', {}).get('x', 0),
            data.get('acceleration', {}).get('y', 0),
            data.get('acceleration', {}).get('z', 0),
            data.get('speed', {}).get('horizontal', 0),
            data.get('speed', {}).get('total', 0),
            data.get('altitude', {}).get('current', 0),
            data.get('battery', 0),
            data.get('battery_temperature', 25),
            data.get('battery_health', 100),
            data.get('flight_time', 0),
            data.get('distance_travelled', 0),
            data.get('distance_from_home', 0),
            data.get('wind', {}).get('speed_x', 0),
            data.get('wind', {}).get('speed_y', 0),
            data.get('signal', {}).get('strength', 1),
            data.get('signal', {}).get('quality', 'Excellent'),
            data.get('mission', {}).get('status', 'IDLE'),
            data.get('mission', {}).get('current_waypoint_index', 0),
            1 if data.get('emergency', {}).get('active', False) else 0
        ))
        
        conn.commit()
        conn.close()
        
    def get_telemetry(self, flight_id: str, limit: int = 1000) -> List[Dict[str, Any]]:
        """Retrieve telemetry data for a flight"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT * FROM telemetry 
            WHERE flight_id = ? 
            ORDER BY timestamp DESC 
            LIMIT ?
        ''', (flight_id, limit))
        
        rows = cursor.fetchall()
        conn.close()
        
        return [dict(row) for row in rows]
        
    def get_flights(self) -> List[Dict[str, Any]]:
        """Get list of all recorded flights"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        cursor.execute('SELECT * FROM flights ORDER BY start_time DESC')
        rows = cursor.fetchall()
        conn.close()
        
        return [dict(row) for row in rows]
        
    def save_flight_summary(self, flight_id: str, data: Dict[str, Any]) -> None:
        """Save flight summary data"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT OR REPLACE INTO flights (
                id, start_time, end_time, duration, distance,
                max_altitude, max_speed, avg_battery, waypoints, status
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            flight_id,
            data.get('start_time', 0),
            data.get('end_time', 0),
            data.get('duration', 0),
            data.get('distance', 0),
            data.get('max_altitude', 0),
            data.get('max_speed', 0),
            data.get('avg_battery', 0),
            data.get('waypoints', 0),
            data.get('status', 'COMPLETED')
        ))
        
        conn.commit()
        conn.close()
        
    def export_to_json(self, flight_id: str, output_path: str) -> None:
        """Export telemetry data to JSON file"""
        data = self.get_telemetry(flight_id)
        with open(output_path, 'w') as f:
            json.dump(data, f, indent=2)