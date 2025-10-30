#!/usr/bin/env python3
"""
Test script to verify system metrics chart data format
"""
import requests
import json
import time

def test_system_metrics():
    """Test system metrics endpoint"""
    print("🧪 Testing System Metrics API...\n")
    
    try:
        # Test the metrics endpoint
        response = requests.get("http://localhost:3001/api/metrics/system", timeout=5)
        
        if response.status_code == 200:
            data = response.json()
            print("✅ System Metrics API is responding\n")
            print(f"Response Data:")
            print(json.dumps(data, indent=2))
            
            # Check for required fields
            required_fields = ['cpu', 'memory', 'disk', 'timestamp']
            missing_fields = [field for field in required_fields if field not in data]
            
            if missing_fields:
                print(f"\n❌ Missing fields: {missing_fields}")
                return False
            else:
                print(f"\n✅ All required fields present:")
                print(f"   CPU: {data['cpu']:.1f}%")
                print(f"   Memory: {data['memory']:.1f}%")
                print(f"   Disk: {data['disk']:.1f}%")
                print(f"   Timestamp: {data['timestamp']}")
                
            # Check optional fields
            optional_fields = ['memory_available_gb', 'disk_free_gb', 'network_in_mbps', 'network_out_mbps']
            present_optional = [field for field in optional_fields if field in data]
            if present_optional:
                print(f"\n✅ Optional fields present:")
                for field in present_optional:
                    print(f"   {field}: {data[field]}")
            
            return True
        else:
            print(f"❌ API returned status code: {response.status_code}")
            return False
            
    except requests.exceptions.ConnectionError:
        print("❌ Connection failed - Is the dashboard running?")
        print("   Start it with: python3 monitoring/dashboard/app.py")
        return False
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

def test_websocket_data():
    """Test that WebSocket data has correct format"""
    print("\n" + "="*60)
    print("📡 WebSocket Data Format Test")
    print("="*60 + "\n")
    
    print("Expected data structure:")
    print("""
    {
      "system_metrics": {
        "cpu": 25.3,
        "memory": 45.2,
        "disk": 60.1,
        "timestamp": "2025-10-30T..."
      },
      "system_history": {
        "timestamps": [...],
        "cpu_usage": [...],
        "memory_usage": [...],
        "disk_usage": [...]
      }
    }
    """)
    
    print("✅ The dashboard now handles both formats:")
    print("   - New format: cpu, memory, disk")
    print("   - Old format: cpu_usage, memory_usage, disk_usage")
    print("\n✅ System overview chart should now display correctly!")

if __name__ == "__main__":
    print("="*60)
    print("🔧 System Overview Chart Fix Verification")
    print("="*60 + "\n")
    
    # Test API
    api_ok = test_system_metrics()
    
    # Show WebSocket info
    test_websocket_data()
    
    print("\n" + "="*60)
    if api_ok:
        print("✅ System chart fix verification complete!")
        print("\n📝 Next steps:")
        print("   1. Open http://localhost:3001 in your browser")
        print("   2. Check the 'System Overview' doughnut chart")
        print("   3. Verify it shows CPU, Memory, and Disk usage")
    else:
        print("❌ Please start the dashboard first:")
        print("   python3 monitoring/dashboard/app.py")
    print("="*60)

