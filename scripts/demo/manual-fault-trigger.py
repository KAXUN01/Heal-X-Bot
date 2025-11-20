#!/usr/bin/env python3
"""
Manual Fault Trigger Script
Allows manual injection of specific fault types for testing
"""

import sys
import argparse
from pathlib import Path

# Add parent directories to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root / 'monitoring' / 'server'))

from fault_injector import initialize_fault_injector, get_fault_injector

def main():
    parser = argparse.ArgumentParser(description='Manual Fault Injection Tool')
    parser.add_argument('--type', choices=['crash', 'cpu', 'memory', 'disk', 'network'],
                       required=True, help='Type of fault to inject')
    parser.add_argument('--container', default='cloud-sim-api-server',
                       help='Container name (for crash/network faults)')
    parser.add_argument('--port', type=int, help='Port number (for network faults)')
    parser.add_argument('--duration', type=int, default=60,
                       help='Duration in seconds (for CPU exhaustion)')
    parser.add_argument('--size', type=float, default=2.0,
                       help='Size in GB (for memory/disk exhaustion)')
    
    args = parser.parse_args()
    
    print(f"\n💥 Injecting {args.type} fault...\n")
    
    fault_injector = initialize_fault_injector()
    
    if args.type == 'crash':
        success, message = fault_injector.inject_service_crash(args.container)
    elif args.type == 'cpu':
        success, message = fault_injector.inject_cpu_exhaustion(args.duration)
    elif args.type == 'memory':
        success, message = fault_injector.inject_memory_exhaustion(args.size)
    elif args.type == 'disk':
        success, message = fault_injector.inject_disk_full(args.size)
    elif args.type == 'network':
        success, message = fault_injector.inject_network_issue(args.container, args.port)
    else:
        print(f"❌ Unknown fault type: {args.type}")
        return
    
    if success:
        print(f"✅ {message}")
        print("\n🔍 Fault detection should trigger within 30 seconds")
        print("🤖 Auto-healing will attempt to fix the issue")
    else:
        print(f"❌ {message}")

if __name__ == "__main__":
    main()

