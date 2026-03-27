import time
import psutil

def get_system_metrics():
    start = time.time()
    
    cpu_percent = psutil.cpu_percent(interval=None)
    memory = psutil.virtual_memory()
    disk = psutil.disk_usage('/')
    
    net_io = psutil.net_io_counters()
    
    print(f"Metrics elapsed: {time.time() - start:.4f}s")

get_system_metrics()

def auto_detect_resource_hogs():
    start = time.time()
    for proc in psutil.process_iter(['pid', 'name', 'cpu_percent', 'memory_percent']):
        pass
    print(f"Hogs elapsed: {time.time() - start:.4f}s")
    
auto_detect_resource_hogs()
