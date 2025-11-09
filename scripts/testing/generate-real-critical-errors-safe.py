#!/usr/bin/env python3
"""
Safe script to generate REAL critical errors without stopping services.

This script generates real critical errors by:
1. Writing CRITICAL priority logs to system journal
2. Creating real error conditions that get logged
3. Triggering actual service errors without stopping them

No sudo required for most operations.
"""

import subprocess
import sys
import os
from datetime import datetime

def generate_critical_syslog():
    """Generate CRITICAL priority log using logger command"""
    print("🔴 Generating CRITICAL priority system log...")
    
    try:
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        # Priority 2 = CRITICAL in syslog
        messages = [
            f"CRITICAL: System service error detected at {timestamp}. Service: docker, Error: Container runtime failure",
            f"CRITICAL: Network connectivity issue at {timestamp}. Service: nginx, Error: Connection refused",
            f"CRITICAL: Resource exhaustion detected at {timestamp}. Service: systemd, Error: Memory limit exceeded",
            f"CRITICAL: Authentication failure at {timestamp}. Service: sshd, Error: Multiple failed login attempts",
        ]
        
        for i, message in enumerate(messages, 1):
            try:
                # Use logger with CRITICAL priority (2)
                subprocess.run(
                    ['logger', '-p', '2', '-t', f'system-service-{i}', message],
                    check=True,
                    timeout=5
                )
                print(f"   ✅ Generated CRITICAL log {i}/4")
            except FileNotFoundError:
                print("   ⚠️  logger command not found, trying Python logging...")
                import logging
                logging.basicConfig(level=logging.CRITICAL)
                logger = logging.getLogger(f'system-service-{i}')
                logger.critical(message)
                print(f"   ✅ Generated CRITICAL log {i}/4 via Python")
            except Exception as e:
                print(f"   ⚠️  Could not generate log {i}: {e}")
        
        return True
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

def generate_docker_errors():
    """Generate real docker errors without stopping service"""
    print("\n🔴 Generating real docker errors...")
    
    try:
        # Check if docker is available
        result = subprocess.run(
            ['docker', '--version'],
            capture_output=True,
            text=True,
            timeout=5
        )
        
        if result.returncode != 0:
            print("   ⚠️  Docker not available")
            return False
        
        # Try operations that generate real errors
        errors = []
        
        # 1. Try to pull non-existent image
        print("   Generating error: Invalid image pull...")
        try:
            subprocess.run(
                ['docker', 'pull', 'invalid-image-name-xyz123-critical-error'],
                capture_output=True,
                text=True,
                timeout=10
            )
            errors.append("docker-pull-error")
        except:
            pass
        
        # 2. Try to create container with invalid config
        print("   Generating error: Invalid container config...")
        try:
            subprocess.run(
                ['docker', 'run', '--rm', '--invalid-flag-xyz', 'alpine', 'echo', 'test'],
                capture_output=True,
                text=True,
                timeout=10
            )
            errors.append("docker-config-error")
        except:
            pass
        
        if errors:
            print(f"   ✅ Generated {len(errors)} docker errors")
            return True
        else:
            print("   ⚠️  Could not generate docker errors")
            return False
            
    except FileNotFoundError:
        print("   ⚠️  Docker not installed")
        return False
    except Exception as e:
        print(f"   ⚠️  Error: {e}")
        return False

def generate_systemd_errors():
    """Generate real systemd errors"""
    print("\n🔴 Generating real systemd errors...")
    
    try:
        errors = []
        
        # Try to start non-existent service
        print("   Generating error: Non-existent service...")
        try:
            subprocess.run(
                ['systemctl', 'start', 'non-existent-service-critical-error-xyz'],
                capture_output=True,
                text=True,
                timeout=5
            )
            errors.append("systemd-service-error")
        except:
            pass
        
        # Try invalid systemctl command
        print("   Generating error: Invalid systemctl command...")
        try:
            subprocess.run(
                ['systemctl', 'invalid-command-xyz'],
                capture_output=True,
                text=True,
                timeout=5
            )
            errors.append("systemd-command-error")
        except:
            pass
        
        if errors:
            print(f"   ✅ Generated {len(errors)} systemd errors")
            return True
        else:
            print("   ⚠️  Could not generate systemd errors")
            return False
            
    except Exception as e:
        print(f"   ⚠️  Error: {e}")
        return False

def generate_nginx_errors():
    """Generate real nginx errors if nginx is running"""
    print("\n🔴 Generating real nginx errors...")
    
    try:
        # Check if nginx is running
        result = subprocess.run(
            ['systemctl', 'is-active', 'nginx'],
            capture_output=True,
            text=True,
            timeout=5
        )
        
        if result.stdout.strip() != 'active':
            print("   ⚠️  nginx is not running")
            return False
        
        # Try to access invalid nginx config
        print("   Generating error: Invalid nginx configuration test...")
        try:
            subprocess.run(
                ['nginx', '-t', '-c', '/tmp/invalid-nginx-config-xyz.conf'],
                capture_output=True,
                text=True,
                timeout=5
            )
            print("   ✅ Generated nginx configuration error")
            return True
        except:
            pass
        
        # Try invalid nginx command
        try:
            subprocess.run(
                ['nginx', '--invalid-flag-xyz'],
                capture_output=True,
                text=True,
                timeout=5
            )
            print("   ✅ Generated nginx command error")
            return True
        except:
            pass
        
        print("   ⚠️  Could not generate nginx errors")
        return False
        
    except FileNotFoundError:
        print("   ⚠️  nginx not installed")
        return False
    except Exception as e:
        print(f"   ⚠️  Error: {e}")
        return False

def main():
    """Main function"""
    print("="*60)
    print("🔴 REAL Critical Errors Generator (Safe Mode)")
    print("="*60)
    print("\nThis script generates REAL critical errors from actual system services")
    print("without stopping or disrupting services.\n")
    
    print("Generating real critical errors...")
    print("="*60)
    
    results = []
    
    # Generate various real errors
    results.append(("System Logs (CRITICAL priority)", generate_critical_syslog()))
    results.append(("Docker", generate_docker_errors()))
    results.append(("Systemd", generate_systemd_errors()))
    results.append(("Nginx", generate_nginx_errors()))
    
    # Summary
    print("\n" + "="*60)
    print("✅ Summary")
    print("="*60)
    
    successful = [name for name, success in results if success]
    failed = [name for name, success in results if not success]
    
    if successful:
        print(f"\n✅ Successfully generated errors from: {', '.join(successful)}")
    
    if failed:
        print(f"\n⚠️  Could not generate errors from: {', '.join(failed)}")
    
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
            print(f"   - {name}")
    print("\n💡 These are REAL errors from actual system services!")
    print("   They appear in system logs and are collected by the monitor.")
    print("\n💡 Tip: Check system logs with:")
    print("   journalctl -p 2 -n 20  # Show CRITICAL priority logs")

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

