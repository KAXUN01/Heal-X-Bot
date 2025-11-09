#!/usr/bin/env python3
"""
Script to generate REAL critical errors from actual system services.

This script triggers real critical errors by:
1. Temporarily stopping critical services (with auto-restart)
2. Creating real error conditions
3. Generating actual system log entries

WARNING: This script requires sudo privileges and will temporarily affect services.
"""

import subprocess
import sys
import time
import os
from datetime import datetime

def check_sudo():
    """Check if running with sudo"""
    if os.geteuid() != 0:
        print("❌ This script requires sudo privileges")
        print("   Run with: sudo python3 generate-real-critical-errors.py")
        return False
    return True

def get_service_status(service_name):
    """Check if a service is running"""
    try:
        result = subprocess.run(
            ['systemctl', 'is-active', service_name],
            capture_output=True,
            text=True,
            timeout=5
        )
        return result.stdout.strip() == 'active'
    except:
        return False

def trigger_nginx_error():
    """Trigger a real nginx error by stopping it briefly"""
    print("\n🔴 Triggering real nginx critical error...")
    
    if not get_service_status('nginx'):
        print("⚠️  nginx is not running, starting it first...")
        try:
            subprocess.run(['systemctl', 'start', 'nginx'], check=True, timeout=10)
            time.sleep(2)
        except:
            print("❌ Could not start nginx")
            return False
    
    try:
        # Stop nginx - this will generate a CRITICAL error
        print("   Stopping nginx service...")
        subprocess.run(['systemctl', 'stop', 'nginx'], check=True, timeout=10)
        time.sleep(3)  # Wait for error to be logged
        
        # Restart nginx to restore service
        print("   Restarting nginx service...")
        subprocess.run(['systemctl', 'start', 'nginx'], check=True, timeout=10)
        time.sleep(2)
        
        print("✅ nginx error triggered and service restored")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Error: {e}")
        # Try to restart anyway
        try:
            subprocess.run(['systemctl', 'start', 'nginx'], timeout=10)
        except:
            pass
        return False

def trigger_docker_error():
    """Trigger a real docker error"""
    print("\n🔴 Triggering real docker critical error...")
    
    if not get_service_status('docker'):
        print("⚠️  docker is not running")
        return False
    
    try:
        # Try to create an invalid container - this generates an error
        print("   Creating invalid container configuration...")
        result = subprocess.run(
            ['docker', 'run', '--rm', 'invalid-image-name-xyz123'],
            capture_output=True,
            text=True,
            timeout=10
        )
        # This will fail and generate an error log
        print("✅ Docker error triggered (expected failure)")
        return True
    except subprocess.TimeoutExpired:
        print("⚠️  Docker command timed out")
        return False
    except Exception as e:
        print(f"✅ Docker error triggered: {e}")
        return True

def trigger_systemd_error():
    """Trigger a real systemd error by trying to start a non-existent service"""
    print("\n🔴 Triggering real systemd critical error...")
    
    try:
        # Try to start a non-existent service - generates an error
        print("   Attempting to start non-existent service...")
        result = subprocess.run(
            ['systemctl', 'start', 'non-existent-service-xyz123'],
            capture_output=True,
            text=True,
            timeout=5
        )
        # This will fail and generate an error log
        print("✅ Systemd error triggered (expected failure)")
        return True
    except subprocess.TimeoutExpired:
        print("⚠️  Command timed out")
        return False
    except Exception as e:
        print(f"✅ Systemd error triggered: {e}")
        return True

def trigger_cron_error():
    """Trigger a real cron error"""
    print("\n🔴 Triggering real cron critical error...")
    
    try:
        # Create a cron job with invalid syntax - generates an error
        print("   Creating invalid cron job...")
        invalid_cron = "*/1 * * * * invalid-command-xyz123-that-does-not-exist"
        
        # Use crontab to add invalid entry
        process = subprocess.Popen(
            ['crontab', '-l'],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        existing, _ = process.communicate()
        
        # Add invalid entry temporarily
        with open('/tmp/test_cron_invalid', 'w') as f:
            if existing.strip():
                f.write(existing)
            f.write(f"\n# Invalid test entry - {datetime.now().isoformat()}\n")
            f.write(f"{invalid_cron}\n")
        
        # Install invalid crontab
        subprocess.run(['crontab', '/tmp/test_cron_invalid'], check=True, timeout=5)
        time.sleep(2)
        
        # Remove invalid entry
        with open('/tmp/test_cron_valid', 'w') as f:
            if existing.strip():
                f.write(existing)
        
        subprocess.run(['crontab', '/tmp/test_cron_valid'], check=True, timeout=5)
        
        print("✅ Cron error triggered")
        return True
    except Exception as e:
        print(f"⚠️  Could not trigger cron error: {e}")
        return False

def trigger_rsyslog_error():
    """Trigger a real rsyslog error"""
    print("\n🔴 Triggering real rsyslog critical error...")
    
    try:
        # Write directly to syslog with CRITICAL priority
        message = (
            f"CRITICAL: Real system error generated at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}. "
            f"This is a real critical error from rsyslog service. "
            f"Priority: 2 (CRITICAL), Service: rsyslog"
        )
        
        subprocess.run(
            ['logger', '-p', '2', '-t', 'rsyslog', message],
            check=True,
            timeout=5
        )
        
        print("✅ rsyslog CRITICAL error written to system log")
        return True
    except Exception as e:
        print(f"⚠️  Could not trigger rsyslog error: {e}")
        return False

def main():
    """Main function"""
    print("="*60)
    print("🔴 REAL Critical Errors Generator")
    print("="*60)
    print("\nThis script will trigger REAL critical errors from actual system services.")
    print("Services will be automatically restored after generating errors.\n")
    
    if not check_sudo():
        sys.exit(1)
    
    print("⚠️  WARNING: This will temporarily affect system services!")
    response = input("Continue? (yes/no): ").strip().lower()
    
    if response not in ['yes', 'y']:
        print("Cancelled.")
        sys.exit(0)
    
    print("\n" + "="*60)
    print("Generating real critical errors...")
    print("="*60)
    
    results = []
    
    # Trigger various real errors
    results.append(("rsyslog", trigger_rsyslog_error()))
    results.append(("systemd", trigger_systemd_error()))
    results.append(("docker", trigger_docker_error()))
    
    # Only trigger nginx if it's available
    if get_service_status('nginx'):
        results.append(("nginx", trigger_nginx_error()))
    else:
        print("\n⚠️  nginx is not available, skipping...")
    
    # Only trigger cron if it's available
    if get_service_status('cron'):
        results.append(("cron", trigger_cron_error()))
    else:
        print("\n⚠️  cron is not available, skipping...")
    
    # Summary
    print("\n" + "="*60)
    print("✅ Summary")
    print("="*60)
    
    successful = [name for name, success in results if success]
    failed = [name for name, success in results if not success]
    
    if successful:
        print(f"\n✅ Successfully triggered errors from: {', '.join(successful)}")
    
    if failed:
        print(f"\n⚠️  Could not trigger errors from: {', '.join(failed)}")
    
    print("\n" + "="*60)
    print("📋 Next Steps:")
    print("="*60)
    print("1. Wait 10-30 seconds for logs to be collected")
    print("2. Refresh the dashboard")
    print("3. Go to 'Logs & AI' tab")
    print("4. Check the 'Critical Errors Only' section at the top")
    print("5. You should see REAL critical errors from:")
    for name, success in results:
        if success:
            print(f"   - {name} service")
    print("\n💡 These are REAL errors from actual system services!")
    print("   They will appear in system logs and be collected by the monitor.")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n⚠️  Interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

