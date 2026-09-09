import json
import time
from datetime import datetime


class MissionRecorder:
    """Records and replays mission flights"""
    
    def __init__(self):
        self.recording = False
        self.recording_data = []
        self.start_time = None
        self.playback = False
        self.playback_index = 0
        self.playback_data = []
        
    def start_recording(self):
        """Start recording mission data"""
        self.recording = True
        self.recording_data = []
        self.start_time = time.time()
        return True
        
    def stop_recording(self):
        """Stop recording and save data"""
        self.recording = False
        if self.recording_data:
            return self.save_recording()
        return None
        
    def record_frame(self, drone_status):
        """Record a single frame of drone data"""
        if not self.recording:
            return
            
        frame = {
            "timestamp": time.time() - self.start_time,
            "position": drone_status["position"],
            "velocity": drone_status["velocity"],
            "speed": drone_status["speed"],
            "battery": drone_status["battery"],
            "state": drone_status["state"],
            "altitude": drone_status["altitude"]
        }
        self.recording_data.append(frame)
        
    def save_recording(self):
        """Save recording to file"""
        if not self.recording_data:
            return None
            
        filename = f"mission_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        data = {
            "metadata": {
                "start_time": self.start_time,
                "duration": self.recording_data[-1]["timestamp"] if self.recording_data else 0,
                "frames": len(self.recording_data)
            },
            "frames": self.recording_data
        }
        
        with open(filename, 'w') as f:
            json.dump(data, f, indent=2)
            
        return filename
        
    def load_recording(self, filename):
        """Load a recorded mission for playback"""
        try:
            with open(filename, 'r') as f:
                data = json.load(f)
                self.playback_data = data["frames"]
                return True
        except Exception as e:
            print(f"Failed to load recording: {e}")
            return False
            
    def start_playback(self):
        """Start playback of recorded mission"""
        if not self.playback_data:
            return False
            
        self.playback = True
        self.playback_index = 0
        return True
        
    def stop_playback(self):
        """Stop playback"""
        self.playback = False
        self.playback_index = 0
        
    def get_next_frame(self, delta_time=0.1):
        """Get the next frame during playback"""
        if not self.playback or self.playback_index >= len(self.playback_data):
            return None
            
        frame = self.playback_data[self.playback_index]
        self.playback_index += 1
        
        # Add timestamp for smooth playback
        frame["replay_time"] = frame["timestamp"]
        
        return frame
        
    def get_playback_progress(self):
        """Get playback progress (0-1)"""
        if not self.playback_data:
            return 0
        return self.playback_index / len(self.playback_data)