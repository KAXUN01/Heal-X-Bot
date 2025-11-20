#!/usr/bin/env python3
"""
Automated Demo Script - Demonstrates Full Healing Cycle
Injects faults and shows the complete detection → diagnosis → healing process
"""

import sys
import time
import requests
import json
from pathlib import Path

# Add parent directories to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root / 'monitoring' / 'server'))

from fault_injector import initialize_fault_injector, get_fault_injector
from fault_detector import initialize_fault_detector, get_fault_detector
from auto_healer import initialize_auto_healer, get_auto_healer
from container_healer import initialize_container_healer, get_container_healer
from root_cause_analyzer import initialize_root_cause_analyzer, get_root_cause_analyzer
from gemini_log_analyzer import initialize_gemini_analyzer

def print_banner():
    """Print demo banner"""
    print("\n" + "="*70)
    print("🤖 AI BOT PROTOTYPE - AUTOMATED HEALING DEMONSTRATION")
    print("="*70)
    print("\nThis demo will:")
    print("  1. Inject a service crash fault")
    print("  2. Show real-time fault detection")
    print("  3. Display AI-powered root cause analysis")
    print("  4. Demonstrate automatic self-healing")
    print("  5. Verify the healing was successful")
    print("\n" + "="*70 + "\n")

def wait_for_detection(fault_detector, timeout=60):
    """Wait for fault to be detected"""
    print("🔍 Waiting for fault detection...")
    start_time = time.time()
    
    while time.time() - start_time < timeout:
        faults = fault_detector.get_detected_faults(limit=5)
        if faults:
            print(f"✅ Fault detected: {faults[-1].get('type')} - {faults[-1].get('message', '')[:50]}")
            return faults[-1]
        time.sleep(2)
        print(".", end="", flush=True)
    
    print("\n⚠️  Timeout waiting for fault detection")
    return None

def main():
    """Main demo function"""
    print_banner()
    
    # Initialize components
    print("🔧 Initializing components...")
    
    # Initialize fault injector
    fault_injector = initialize_fault_injector()
    print("  ✅ Fault injector initialized")
    
    # Initialize fault detector
    fault_detector = initialize_fault_detector()
    fault_detector.start_monitoring(interval=10)  # Check every 10 seconds for demo
    print("  ✅ Fault detector started")
    
    # Initialize AI components
    gemini_analyzer = initialize_gemini_analyzer()
    root_cause_analyzer = initialize_root_cause_analyzer(gemini_analyzer=gemini_analyzer)
    print("  ✅ AI analyzers initialized")
    
    # Initialize healers
    container_healer = initialize_container_healer()
    auto_healer = initialize_auto_healer(
        gemini_analyzer=gemini_analyzer,
        container_healer=container_healer,
        root_cause_analyzer=root_cause_analyzer
    )
    print("  ✅ Auto-healer initialized")
    
    print("\n" + "-"*70)
    print("STEP 1: Injecting Service Crash Fault")
    print("-"*70)
    
    # Inject service crash
    container_name = "cloud-sim-api-server"
    print(f"\n💥 Injecting crash for container: {container_name}")
    success, message = fault_injector.inject_service_crash(container_name)
    
    if success:
        print(f"✅ {message}")
    else:
        print(f"❌ Failed to inject fault: {message}")
        print("   Make sure cloud simulation services are running:")
        print("   docker compose -f config/docker-compose-cloud-sim.yml up -d")
        print("   # Or use: docker-compose -f config/docker-compose-cloud-sim.yml up -d")
        return
    
    print("\n" + "-"*70)
    print("STEP 2: Waiting for Fault Detection")
    print("-"*70)
    
    # Wait for detection
    detected_fault = wait_for_detection(fault_detector, timeout=30)
    
    if not detected_fault:
        print("❌ Fault was not detected. Check fault detector configuration.")
        return
    
    print("\n" + "-"*70)
    print("STEP 3: AI-Powered Root Cause Analysis")
    print("-"*70)
    
    # Analyze fault
    print("\n🧠 Analyzing fault with AI...")
    analysis = root_cause_analyzer.analyze_fault(detected_fault)
    
    print(f"\n📊 Root Cause: {analysis.get('root_cause', 'Unknown')}")
    print(f"📈 Confidence: {analysis.get('confidence', 0) * 100:.0f}%")
    print(f"🏷️  Classification: {analysis.get('fault_classification', 'Unknown')}")
    
    if analysis.get('recommended_actions'):
        print("\n💡 Recommended Actions:")
        for i, action in enumerate(analysis.get('recommended_actions', []), 1):
            print(f"   {i}. {action}")
    
    print("\n" + "-"*70)
    print("STEP 4: Automatic Self-Healing")
    print("-"*70)
    
    # Attempt healing
    print("\n🔧 Attempting automatic healing...")
    healing_result = auto_healer.heal_cloud_fault(detected_fault)
    
    print(f"\n📋 Healing Status: {healing_result.get('status', 'unknown')}")
    
    if healing_result.get('actions'):
        print("\n⚙️  Actions Taken:")
        for i, action in enumerate(healing_result.get('actions', []), 1):
            status_emoji = "✅" if action.get('success') else "❌"
            print(f"   {i}. {status_emoji} {action.get('action', {}).get('description', 'Unknown action')}")
    
    if healing_result.get('success'):
        print("\n✅ Healing successful!")
    else:
        print("\n❌ Auto-healing failed or incomplete")
        
        if healing_result.get('manual_instructions'):
            print("\n📖 Manual Instructions:")
            print(healing_result.get('manual_instructions'))
    
    print("\n" + "-"*70)
    print("STEP 5: Verification")
    print("-"*70)
    
    # Verify healing
    if healing_result.get('verification'):
        verification = healing_result.get('verification')
        if verification.get('success'):
            print(f"\n✅ Verification: {verification.get('details', 'Healing verified')}")
        else:
            print(f"\n⚠️  Verification: {verification.get('details', 'Healing not verified')}")
    
    # Check container status
    if container_healer:
        health = container_healer.verify_container_health(container_name)
        if health.get('is_running'):
            print(f"\n✅ Container {container_name} is running")
        else:
            print(f"\n❌ Container {container_name} is not running")
    
    print("\n" + "="*70)
    print("🎉 DEMO COMPLETE!")
    print("="*70)
    print("\nView the dashboard at: http://localhost:5001")
    print("Check Discord for notifications (if configured)")
    print("\n")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n⚠️  Demo interrupted by user")
    except Exception as e:
        print(f"\n❌ Error during demo: {e}")
        import traceback
        traceback.print_exc()

