
import sys
import os
import time
import json
import logging

# Add server directory to path
sys.path.append('/home/kasun/Documents/Heal-X-Bot/monitoring/server')

# Mock configuration
os.environ['GROQ_API_KEY'] = 'mock_key'

def test_service_discovery():
    print("\n[1] Testing Service Discovery Optimization...")
    start_time = time.time()
    try:
        from service_discovery import ServiceDiscovery
        discovery = ServiceDiscovery()
        # Mocking log locations to avoid full scan in test environment if needed, 
        # but we want to test the scan speed.
        # However, we should be careful not to scan too much if running in this environment.
        # The fixes limited the depth, so it should be safe.
        print("    Running discover_all_log_locations...")
        discovery.discover_all_log_locations()
        duration = time.time() - start_time
        print(f"    ✅ Discovery completed in {duration:.2f} seconds")
        
        # Verify specific findings
        log_count = sum(len(logs) for logs in discovery.log_locations.values())
        print(f"    Found {log_count} log files across {len(discovery.log_locations)} services")
        
    except Exception as e:
        print(f"    ❌ Error in service discovery: {e}")

def test_log_pagination():
    print("\n[2] Testing Centralized Logger Pagination...")
    try:
        from centralized_logger import initialize_centralized_logging, centralized_logger
        
        # Initialize
        initialize_centralized_logging()
        # It runs a thread, but we can usage the methods directly.
        # We need to populate some dummy logs if empty?
        # Or rely on existing logs if any.
        
        # Let's manually inject some logs for testing
        print("    Injecting test logs...")
        base_time = time.time()
        for i in range(20):
            centralized_logger.log_index.append({
                'timestamp': '2025-01-01T12:00:{:02d}'.format(i),
                'service': 'test_service',
                'message': f'Log message {i}',
                'level': 'INFO',
                'source_file': 'test.log'
            })
            
        # Test Page 1 (Limit 5, Offset 0)
        page1 = centralized_logger.get_recent_logs(limit=5, offset=0)
        print(f"    Page 1 (Limit 5): Got {len(page1)} logs")
        
        # Test Page 2 (Limit 5, Offset 5)
        page2 = centralized_logger.get_recent_logs(limit=5, offset=5)
        print(f"    Page 2 (Limit 5): Got {len(page2)} logs")
        
        # Verify content
        # get_recent_logs sorts by timestamp desc.
        # Log 19 is newest.
        # Page 1 should have 19, 18, 17, 16, 15
        # Page 2 should have 14, 13, 12, 11, 10
        
        first_msg = page1[0]['message'] if page1 else "None"
        second_page_first_msg = page2[0]['message'] if page2 else "None"
        
        print(f"    Page 1 first log: {first_msg}")
        print(f"    Page 2 first log: {second_page_first_msg}")
        
        if first_msg == 'Log message 19' and second_page_first_msg == 'Log message 14':
            print("    ✅ Pagination logic verifies correctly")
        else:
            print("    ❌ Pagination logic mismatch")
            
    except Exception as e:
        print(f"    ❌ Error testing pagination: {e}")

if __name__ == "__main__":
    print("starting Verification Script...")
    test_service_discovery()
    test_log_pagination()
    print("\nVerification Complete.")
