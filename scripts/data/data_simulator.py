import numpy as np
from datetime import datetime, timedelta
from typing import List, Tuple
import time


class MetricSimulator:
    """Generate realistic metric data with seasonality, trends, and anomalies"""

    def __init__(self, seed: int = 42):
        np.random.seed(seed)

    def generate_cpu_usage(self, num_points: int = 1000) -> List[Tuple[float, bool]]:
        """
        Generate CPU usage metrics with:
        - Daily seasonality (higher during business hours)
        - Gradual trend
        - Random walk
        - Occasional spikes (anomalies)
        
        Returns: List of (value, is_anomaly) tuples
        """
        
        data = []
        base = 30
        
        for i in range(num_points):
            # Daily seasonality (8am-6pm higher)
            hour = (i % 24)
            seasonality = 15 * np.sin((hour - 8) * np.pi / 12) if 8 <= hour <= 18 else 0
            
            # Trend
            trend = 0.02 * i
            
            # Random walk
            random_walk = np.random.normal(0, 1)
            
            # Combine
            value = base + seasonality + trend + random_walk
            value = np.clip(value, 0, 100)
            
            # Mark anomalies (spikes)
            is_anomaly = False
            if np.random.random() < 0.02:  # 2% anomaly rate
                value = np.clip(np.random.uniform(80, 100), 0, 100)
                is_anomaly = True
            
            data.append((float(value), is_anomaly))
        
        return data

    def generate_memory_usage(self, num_points: int = 1000) -> List[Tuple[float, bool]]:
        """Memory usage with gradual degradation and occasional spikes"""
        
        data = []
        base = 50
        
        for i in range(num_points):
            # Gradual increase (memory leak)
            trend = 0.01 * i
            
            # Periodic drops (garbage collection)
            gc_effect = -10 * np.sin((i % 200) * 2 * np.pi / 200) if (i % 200) < 10 else 0
            
            # Random noise
            noise = np.random.normal(0, 2)
            
            value = base + trend + gc_effect + noise
            value = np.clip(value, 0, 100)
            
            # Mark anomalies (OOM risk)
            is_anomaly = False
            if np.random.random() < 0.015:
                value = np.clip(np.random.uniform(85, 100), 0, 100)
                is_anomaly = True
            
            data.append((float(value), is_anomaly))
        
        return data

    def generate_api_latency(self, num_points: int = 1000) -> List[Tuple[float, bool]]:
        """API latency with traffic correlation and occasional degradation"""
        
        data = []
        base = 100  # milliseconds
        
        for i in range(num_points):
            # Business hours increase latency
            hour = (i % 24)
            traffic = 50 * np.sin((hour - 8) * np.pi / 12) if 8 <= hour <= 18 else 0
            
            # Trend degradation over time
            degradation = 0.05 * i
            
            # Random noise
            noise = np.random.normal(0, 20)
            
            value = base + traffic + degradation + noise
            value = np.clip(value, 10, 5000)
            
            # Mark anomalies (spikes)
            is_anomaly = False
            if np.random.random() < 0.01:
                value = np.random.uniform(1000, 5000)
                is_anomaly = True
            
            data.append((float(value), is_anomaly))
        
        return data

    def generate_disk_io(self, num_points: int = 1000) -> List[Tuple[float, bool]]:
        """Disk I/O with periodic spikes and correlations"""
        
        data = []
        base = 40  # MB/s
        
        for i in range(num_points):
            # Periodic backups (every 300 samples)
            backup_spike = 100 if (i % 300) < 20 else 0
            
            # Random operational I/O
            operational = np.random.exponential(20)
            
            # Noise
            noise = np.random.normal(0, 5)
            
            value = base + backup_spike + operational + noise
            value = np.clip(value, 0, 500)
            
            # Mark anomalies
            is_anomaly = False
            if np.random.random() < 0.01:
                value = np.random.uniform(400, 500)
                is_anomaly = True
            
            data.append((float(value), is_anomaly))
        
        return data

    def generate_request_rate(self, num_points: int = 1000) -> List[Tuple[float, bool]]:
        """Request rate with daily patterns and traffic spikes"""
        
        data = []
        base = 1000  # req/s
        
        for i in range(num_points):
            # Daily seasonality
            hour = (i % 24)
            peak = 2000 * np.sin((hour - 12) * np.pi / 12) if 6 <= hour <= 22 else 500
            
            # Random fluctuation
            fluctuation = np.random.normal(0, 100)
            
            value = base + peak + fluctuation
            value = np.clip(value, 100, 5000)
            
            # Mark anomalies (DDoS-like patterns)
            is_anomaly = False
            if np.random.random() < 0.005:
                value = np.random.uniform(4000, 5000)
                is_anomaly = True
            
            data.append((float(value), is_anomaly))
        
        return data

    def get_all_metrics(self, num_points: int = 1000) -> dict:
        """Generate all metrics"""
        return {
            "cpu_usage": self.generate_cpu_usage(num_points),
            "memory_usage": self.generate_memory_usage(num_points),
            "api_latency": self.generate_api_latency(num_points),
            "disk_io": self.generate_disk_io(num_points),
            "request_rate": self.generate_request_rate(num_points),
        }

    def generate_synthetic_outliers(
        self,
        base_series: List[float],
        outlier_type: str = "spike",
        anomaly_ratio: float = 0.05,
    ) -> List[Tuple[float, bool]]:
        """
        Inject synthetic outliers:
        - 'spike': Global point anomaly
        - 'level_shift': Step increase in metric baseline
        - 'contextual': Low amplitude noise breaking temporal seasonality
        """
        n = len(base_series)
        series = list(base_series)
        anomalies = [False] * n
        num_anomalies = int(n * anomaly_ratio)

        if outlier_type == "spike":
            indices = np.random.choice(n, size=num_anomalies, replace=False)
            std = np.std(series) if np.std(series) > 0 else 1.0
            for idx in indices:
                series[idx] += 5 * std
                anomalies[idx] = True

        elif outlier_type == "level_shift":
            shift_start = n // 2
            std = np.std(series) if np.std(series) > 0 else 1.0
            for i in range(shift_start, min(shift_start + num_anomalies, n)):
                series[i] += 4 * std
                anomalies[i] = True

        elif outlier_type == "contextual":
            # Noise during quiet periods (breaking context)
            indices = np.random.choice(n, size=num_anomalies, replace=False)
            for idx in indices:
                series[idx] += np.random.normal(0, np.std(series) * 2)
                anomalies[idx] = True

        return list(zip(series, anomalies))


def simulate_metrics_stream(duration_hours: int = 24, interval_seconds: int = 60):
    """
    Stream metrics in real-time for testing.
    
    Usage:
        for metric_name, value, is_anomaly in simulate_metrics_stream(duration_hours=1):
            # Ingest metric via API
            pass
    """
    
    simulator = MetricSimulator()
    metrics_data = simulator.get_all_metrics(num_points=int(duration_hours * 3600 / interval_seconds))
    
    start_time = datetime.utcnow()
    
    for i in range(len(next(iter(metrics_data.values())))):
        timestamp = start_time + timedelta(seconds=i * interval_seconds)
        
        for metric_name, data in metrics_data.items():
            value, is_anomaly = data[i]
            yield metric_name, value, is_anomaly, timestamp
        
        # Simulate real-time delay
        time.sleep(interval_seconds / 1000)  # Sleep for smaller fraction


if __name__ == "__main__":
    # Generate sample data
    simulator = MetricSimulator()
    metrics = simulator.get_all_metrics(num_points=100)
    
    print("Sample generated metrics:")
    for metric_name, data in metrics.items():
        values = [v for v, _ in data]
        print(f"{metric_name}: mean={np.mean(values):.2f}, std={np.std(values):.2f}, "
              f"min={np.min(values):.2f}, max={np.max(values):.2f}")
