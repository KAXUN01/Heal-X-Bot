import time
import psutil

def get_top_processes(limit: int = 10):
    start = time.time()
    processes = []
    print("Starting process_iter...")
    for proc in psutil.process_iter(['pid', 'name', 'cpu_percent', 'memory_percent']):
        try:
            pinfo = proc.info
            if pinfo['cpu_percent'] is not None and (pinfo['cpu_percent'] > 0 or pinfo['memory_percent'] > 1):
                processes.append({
                    "pid": pinfo['pid'],
                    "name": pinfo['name'],
                    "cpu": round(pinfo['cpu_percent'], 2) if pinfo['cpu_percent'] is not None else 0,
                    "memory": round(pinfo['memory_percent'], 2) if pinfo['memory_percent'] is not None else 0
                })
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            pass
    print(f"Elapsed: {time.time() - start:.2f}s")
    
get_top_processes()
