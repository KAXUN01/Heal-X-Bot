import threading
import time
import random
import logging

class DDoSSimulator:
    def __init__(self, metrics_registry=None, stats_dict=None, ml_stats_dict=None):
        """
        Initialize the DDoS Simulator.
        
        Args:
            metrics_registry (dict): Dictionary containing Prometheus metric objects (optional).
            stats_dict (dict): Dictionary mirroring ddos_statistics for dashboard (optional).
            ml_stats_dict (dict): Dictionary for ML performance metrics (optional).
        """
        self.metrics = metrics_registry
        self.stats = stats_dict
        self.ml_stats = ml_stats_dict
        self.running = False
        self.thread = None
        self.logger = logging.getLogger(__name__)

    def start_simulation(self):
        """Start the DDoS simulation in a background thread."""
        if self.running:
            return "Simulation already running"
        
        self.running = True
        self.thread = threading.Thread(target=self._simulate_traffic)
        self.thread.daemon = True
        self.thread.start()
        self.logger.info("DDoS Simulation started")
        return "DDoS Simulation started"

    def stop_simulation(self):
        """Stop the DDoS simulation."""
        if not self.running:
            return "Simulation not running"
        
        self.running = False
        if self.thread:
            self.thread.join(timeout=1.0)
        self.logger.info("DDoS Simulation stopped")
        
        # Reset metrics to normal levels
        self._reset_metrics()
        return "DDoS Simulation stopped"

    def is_running(self):
        return self.running

    def _simulate_traffic(self):
        """Generate synthetic traffic patterns."""
        step = 0
        while self.running:
            try:
                # Simulate ramping up traffic
                intensity = min(1.0, step / 10.0)  # Ramp up over 10 steps
                
                # Update Prometheus Metrics if available
                if self.metrics:
                    normal_net_in = random.uniform(1000, 5000)
                    ddos_net_in = intensity * random.uniform(50000000, 100000000)
                    
                    normal_conns = random.randint(10, 50)
                    ddos_conns = int(intensity * random.randint(500, 2000))
                    
                    current_net_in = normal_net_in + ddos_net_in
                    current_conns = normal_conns + ddos_conns
                    
                    if 'NETWORK_IN' in self.metrics:
                        self.metrics['NETWORK_IN'].set(current_net_in)
                    if 'CONNECTIONS' in self.metrics:
                        self.metrics['CONNECTIONS'].set(current_conns)
                    
                    prob = 0.1
                    if current_conns > 500:
                        prob = 0.5 + (0.4 * intensity)
                    elif current_conns > 100:
                        prob = 0.3
                    
                    if 'DDOS_PROBABILITY' in self.metrics:
                        self.metrics['DDOS_PROBABILITY'].set(prob)

                # Update Dashboard Stats if available
                if self.stats is not None:
                    # Update stats based on intensity
                    # Ramp up detections
                    if step % 2 == 0:
                        self.stats['total_detections'] += random.randint(1, 5)
                        self.stats['ddos_attacks'] += random.randint(0, 3)
                        
                        # Set detection rate (simple calc)
                        if self.stats['total_detections'] > 0:
                            self.stats['detection_rate'] = (
                                self.stats['ddos_attacks'] / self.stats['total_detections'] * 100
                            )

                    # Update attack types
                    if intensity > 0.5:
                        self.stats['attack_types']['SYN Flood'] = self.stats['attack_types'].get('SYN Flood', 0) + random.randint(1, 10)
                        self.stats['attack_types']['UDP Flood'] = self.stats['attack_types'].get('UDP Flood', 0) + random.randint(1, 5)

                    # Update source IPs
                    fake_ip = f"192.168.{random.randint(1,255)}.{random.randint(1,255)}"
                    self.stats['top_source_ips'][fake_ip] = self.stats['top_source_ips'].get(fake_ip, 0) + random.randint(100, 1000)

                # Update ML Metrics if available
                if self.ml_stats is not None:
                    # Model performance degrades slightly under load, but throughput increases then drops
                    self.ml_stats['accuracy'] = max(0.85, 0.98 - (0.1 * intensity) + random.uniform(-0.02, 0.02))
                    self.ml_stats['precision'] = max(0.80, 0.95 - (0.15 * intensity) + random.uniform(-0.02, 0.02))
                    self.ml_stats['recall'] = max(0.85, 0.90 - (0.05 * intensity) + random.uniform(-0.02, 0.02))
                    self.ml_stats['f1_score'] = 2 * (self.ml_stats['precision'] * self.ml_stats['recall']) / (self.ml_stats['precision'] + self.ml_stats['recall'])
                    
                    # Latency spikes
                    base_latency = 5.0
                    load_latency = intensity * random.uniform(50, 150)
                    self.ml_stats['prediction_time_ms'] = base_latency + load_latency
                    
                    # Throughput spikes then saturates
                    base_throughput = 200.0
                    load_throughput = intensity * random.uniform(1000, 5000)
                    self.ml_stats['throughput'] = base_throughput + load_throughput

                step += 1
                time.sleep(1)
                
            except Exception as e:
                self.logger.error(f"Error in DDoS simulation: {e}")
                time.sleep(1)

    def _reset_metrics(self):
        """Reset metrics to normal values."""
        if self.metrics:
            if 'DDOS_PROBABILITY' in self.metrics:
                self.metrics['DDOS_PROBABILITY'].set(0.0)
            if 'CONNECTIONS' in self.metrics:
                self.metrics['CONNECTIONS'].set(random.randint(10, 30))
            if 'NETWORK_IN' in self.metrics:
                self.metrics['NETWORK_IN'].set(random.uniform(1000, 2000))


