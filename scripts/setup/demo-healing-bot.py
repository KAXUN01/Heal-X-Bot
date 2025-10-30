#!/usr/bin/env python3
"""
Healing-bot: Demo Script
A simple demonstration of the healing-bot system capabilities.
"""

import time
import requests
import json
from datetime import datetime

def print_banner():
    """Print demo banner"""
    banner = """
╔══════════════════════════════════════════════════════════════╗
║                    🛡️  HEALING-BOT DEMO  🛡️                 ║
║                                                              ║
║              AI-Powered DDoS Detection System                ║
║                                                              ║
║  This demo will show you the system capabilities:           ║
║  • 🧠 ML-based DDoS detection                               ║
║  • 🚫 Automatic IP blocking                                 ║
║  • 📊 Real-time monitoring dashboard                        ║
║  • 🤖 AI-powered incident response                           ║
║  • 📈 Advanced analytics and reporting                      ║
╚══════════════════════════════════════════════════════════════╝
    """
    print(banner)

def check_service_health(service_name, url, timeout=5):
    """Check if a service is healthy"""
    try:
        response = requests.get(url, timeout=timeout)
        if response.status_code == 200:
            print(f"✅ {service_name}: Healthy")
            return True
        else:
            print(f"⚠️  {service_name}: Responding but not healthy (Status: {response.status_code})")
            return False
    except requests.exceptions.RequestException as e:
        print(f"❌ {service_name}: Not responding ({str(e)})")
        return False

def demo_system_capabilities():
    """Demonstrate system capabilities"""
    print("🔍 Checking system health...")
    print("-" * 50)
    
    # Service endpoints
    services = [
        ("Model API", "http://localhost:8080/health"),
        ("Network Analyzer", "http://localhost:8000/active-threats"),
        ("Dashboard", "http://localhost:3001/api/health"),
        ("Incident Bot", "http://localhost:8000/health"),
        ("Monitoring Server", "http://localhost:5000/health")
    ]
    
    healthy_services = 0
    total_services = len(services)
    
    for service_name, url in services:
        if check_service_health(service_name, url):
            healthy_services += 1
        time.sleep(0.5)  # Small delay between checks
    
    print("-" * 50)
    print(f"📊 System Status: {healthy_services}/{total_services} services healthy")
    
    if healthy_services == total_services:
        print("🎉 All services are running perfectly!")
        return True
    elif healthy_services > 0:
        print("⚠️  Some services are running, but not all")
        return False
    else:
        print("❌ No services are responding")
        return False

def demo_features():
    """Demonstrate key features"""
    print("\n🚀 Demonstrating Healing-bot Features")
    print("=" * 60)
    
    features = [
        "🧠 AI-Powered DDoS Detection",
        "🚫 Automatic IP Blocking", 
        "📊 Real-time Dashboard",
        "🤖 Smart Incident Response",
        "📈 Advanced Analytics",
        "🔍 Network Traffic Analysis",
        "🛡️ Multi-layer Security",
        "📱 Web-based Management"
    ]
    
    for i, feature in enumerate(features, 1):
        print(f"{i:2d}. {feature}")
        time.sleep(0.3)
    
    print("\n✨ Key Benefits:")
    benefits = [
        "• Automatic threat detection and response",
        "• Real-time monitoring and alerting", 
        "• AI-powered security recommendations",
        "• Comprehensive analytics and reporting",
        "• Easy-to-use web interface",
        "• Scalable and production-ready"
    ]
    
    for benefit in benefits:
        print(f"   {benefit}")
        time.sleep(0.2)

def show_access_points():
    """Show system access points"""
    print("\n🌐 System Access Points")
    print("=" * 60)
    
    access_points = [
        ("📊 Main Dashboard", "http://localhost:3001", "Primary monitoring interface"),
        ("🤖 ML Model API", "http://localhost:8080", "DDoS detection service"),
        ("🔍 Network Analyzer", "http://localhost:8000", "Traffic analysis & IP blocking"),
        ("🚨 Incident Bot", "http://localhost:8000", "AI incident response"),
        ("📈 Monitoring Server", "http://localhost:5000", "System metrics & health"),
        ("📊 Prometheus", "http://localhost:9090", "Metrics collection (Docker)"),
        ("📈 Grafana", "http://localhost:3000", "Advanced dashboards (Docker)")
    ]
    
    for name, url, description in access_points:
        print(f"{name:<20} {url:<30} {description}")

def show_next_steps():
    """Show next steps for users"""
    print("\n🎯 Next Steps")
    print("=" * 60)
    
    steps = [
        "1. 🌐 Open the main dashboard at http://localhost:3001",
        "2. 🔍 Explore the network analyzer at http://localhost:8000", 
        "3. 🤖 Test the incident bot capabilities",
        "4. 📊 Check the monitoring server metrics",
        "5. 🛡️ Configure your security settings",
        "6. 📈 Set up alerts and notifications"
    ]
    
    for step in steps:
        print(f"   {step}")
        time.sleep(0.2)
    
    print("\n💡 Pro Tips:")
    tips = [
        "• Use the dashboard to monitor system health in real-time",
        "• Configure API keys in the .env file for full functionality",
        "• Check the logs for detailed system information",
        "• Use Docker mode for production deployments",
        "• Use native mode for development and testing"
    ]
    
    for tip in tips:
        print(f"   {tip}")
        time.sleep(0.2)

def main():
    """Main demo function"""
    print_banner()
    
    print("🔄 Checking if Healing-bot is running...")
    print()
    
    # Check system health
    system_healthy = demo_system_capabilities()
    
    # Show features
    demo_features()
    
    # Show access points
    show_access_points()
    
    # Show next steps
    show_next_steps()
    
    print("\n" + "=" * 60)
    if system_healthy:
        print("🎉 Healing-bot is running successfully!")
        print("   You can now access all the features and services.")
    else:
        print("⚠️  Healing-bot is not fully running.")
        print("   Please start the system first with:")
        print("   • Windows: start-healing-bot.bat")
        print("   • Linux/Mac: ./start-healing-bot.sh")
        print("   • Or: python run-healing-bot.py")
    
    print("=" * 60)
    print("🛡️  Thank you for using Healing-bot!")
    print("   Stay protected with AI-powered security!")

if __name__ == "__main__":
    main()
