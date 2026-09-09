import numpy as np
from sklearn.ensemble import IsolationForest
from sklearn.preprocessing import StandardScaler
import joblib
import os


class AnomalyDetector:
    """Machine Learning-based anomaly detection for flight data"""
    
    def __init__(self, model_path: str = None):
        self.model = None
        self.scaler = StandardScaler()
        self.is_trained = False
        self.model_path = model_path
        
        if model_path and os.path.exists(model_path):
            self.load_model(model_path)
    
    def train(self, data: np.ndarray) -> None:
        """Train the anomaly detection model"""
        # Normalize data
        scaled_data = self.scaler.fit_transform(data)
        
        # Train Isolation Forest
        self.model = IsolationForest(
            contamination=0.1,
            random_state=42,
            n_estimators=100
        )
        self.model.fit(scaled_data)
        self.is_trained = True
        
        if self.model_path:
            self.save_model(self.model_path)
    
    def predict(self, data: np.ndarray) -> dict:
        """Predict if data points are anomalies"""
        if not self.is_trained:
            return {"anomaly": False, "score": 0.0}
        
        scaled_data = self.scaler.transform(data.reshape(1, -1))
        prediction = self.model.predict(scaled_data)
        score = self.model.score_samples(scaled_data)[0]
        
        return {
            "anomaly": prediction[0] == -1,
            "score": float(score),
            "confidence": 1.0 if prediction[0] == -1 else 0.5
        }
    
    def save_model(self, path: str) -> None:
        """Save trained model to disk"""
        os.makedirs(os.path.dirname(path), exist_ok=True)
        joblib.dump({
            'model': self.model,
            'scaler': self.scaler
        }, path)
    
    def load_model(self, path: str) -> None:
        """Load trained model from disk"""
        data = joblib.load(path)
        self.model = data['model']
        self.scaler = data['scaler']
        self.is_trained = True


# Generate training data from telemetry
def generate_training_data(telemetry_data: list) -> np.ndarray:
    """Extract features for training"""
    features = []
    
    for record in telemetry_data:
        features.append([
            record.get('position_z', 0),  # Altitude
            record.get('speed_horizontal', 0),  # Speed
            record.get('battery', 100),  # Battery
            record.get('velocity_z', 0),  # Vertical speed
            record.get('acceleration_z', 0),  # Vertical acceleration
            record.get('distance_from_home', 0),  # Distance from home
        ])
    
    return np.array(features)