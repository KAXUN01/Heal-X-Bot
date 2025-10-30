#!/usr/bin/env python3
"""
Environment Setup Helper
Helps you configure your .env file with all necessary API keys and settings
"""

import os
import sys
from pathlib import Path


def print_header():
    """Print welcome header"""
    print("\n" + "="*70)
    print("🔐 AUTOMATIC SELF-HEALING BOT - Environment Setup")
    print("="*70)
    print("\nThis script will help you configure your .env file.\n")


def check_existing_env():
    """Check if .env file already exists"""
    env_file = Path(".env")
    if env_file.exists():
        print("ℹ️  Found existing .env file")
        response = input("Do you want to update it? (y/n): ").lower()
        if response != 'y':
            print("\n✅ Keeping existing .env file")
            sys.exit(0)
        return True
    return False


def create_from_template():
    """Create .env from template"""
    template_file = Path("env.template")
    env_file = Path(".env")
    
    if not template_file.exists():
        print("❌ Error: env.template not found")
        sys.exit(1)
    
    # Copy template to .env
    with open(template_file, 'r') as src:
        content = src.read()
    
    with open(env_file, 'w') as dst:
        dst.write(content)
    
    print("✅ Created .env file from template")


def get_user_input(prompt, required=False, default=""):
    """Get user input with validation"""
    while True:
        if default:
            value = input(f"{prompt} [{default}]: ").strip()
            if not value:
                return default
        else:
            value = input(f"{prompt}: ").strip()
        
        if value or not required:
            return value
        else:
            print("❌ This field is required. Please enter a value.")


def configure_env():
    """Interactive configuration of .env file"""
    config = {}
    
    print("\n" + "-"*70)
    print("🤖 AI Configuration (REQUIRED for AI Log Analysis)")
    print("-"*70)
    print("\nGet your free Gemini API key from:")
    print("👉 https://makersuite.google.com/app/apikey\n")
    
    gemini_key = get_user_input("Enter your Gemini API Key", required=True)
    config['GEMINI_API_KEY'] = gemini_key
    
    print("\n" + "-"*70)
    print("💬 Slack Integration (OPTIONAL)")
    print("-"*70)
    print("\nSlack webhook for alerts and notifications")
    print("Get it from: https://api.slack.com/messaging/webhooks\n")
    
    slack_webhook = get_user_input("Slack Webhook URL (press Enter to skip)")
    if slack_webhook:
        config['SLACK_WEBHOOK'] = slack_webhook
    
    print("\n" + "-"*70)
    print("☁️  AWS S3 Configuration (OPTIONAL)")
    print("-"*70)
    print("\nFor uploading logs to S3\n")
    
    setup_aws = get_user_input("Configure AWS S3? (y/n)", default="n")
    if setup_aws.lower() == 'y':
        config['AWS_ACCESS_KEY_ID'] = get_user_input("AWS Access Key ID", required=True)
        config['AWS_SECRET_ACCESS_KEY'] = get_user_input("AWS Secret Access Key", required=True)
        config['AWS_REGION'] = get_user_input("AWS Region", default="us-east-1")
        config['S3_BUCKET_NAME'] = get_user_input("S3 Bucket Name", required=True)
    
    print("\n" + "-"*70)
    print("📊 Grafana Configuration (OPTIONAL)")
    print("-"*70)
    
    grafana_password = get_user_input("Grafana Admin Password", default="admin")
    config['GRAFANA_ADMIN_PASSWORD'] = grafana_password
    
    print("\n" + "-"*70)
    print("🔧 Port Configuration (OPTIONAL)")
    print("-"*70)
    print("\nDefault ports work for most cases. Press Enter to use defaults.\n")
    
    configure_ports = get_user_input("Configure custom ports? (y/n)", default="n")
    if configure_ports.lower() == 'y':
        config['MODEL_PORT'] = get_user_input("Model API Port", default="8080")
        config['DASHBOARD_PORT'] = get_user_input("Dashboard Port", default="3001")
        config['NETWORK_ANALYZER_PORT'] = get_user_input("Network Analyzer Port", default="8000")
        config['INCIDENT_BOT_PORT'] = get_user_input("Incident Bot Port", default="8000")
        config['MONITORING_SERVER_PORT'] = get_user_input("Monitoring Server Port", default="5000")
    
    return config


def update_env_file(config):
    """Update .env file with configuration"""
    env_file = Path(".env")
    
    # Read current .env
    with open(env_file, 'r') as f:
        lines = f.readlines()
    
    # Update values
    updated_lines = []
    updated_keys = set()
    
    for line in lines:
        if '=' in line and not line.strip().startswith('#'):
            key = line.split('=')[0].strip()
            if key in config:
                updated_lines.append(f"{key}={config[key]}\n")
                updated_keys.add(key)
            else:
                updated_lines.append(line)
        else:
            updated_lines.append(line)
    
    # Add any new keys that weren't in the template
    for key, value in config.items():
        if key not in updated_keys:
            updated_lines.append(f"{key}={value}\n")
    
    # Write back to .env
    with open(env_file, 'w') as f:
        f.writelines(updated_lines)
    
    print("\n✅ Updated .env file successfully!")


def verify_setup():
    """Verify the setup"""
    print("\n" + "="*70)
    print("🔍 Verifying Setup")
    print("="*70)
    
    try:
        from dotenv import load_dotenv
        load_dotenv()
        
        gemini_key = os.getenv('GEMINI_API_KEY')
        if gemini_key and gemini_key != 'your_gemini_api_key_here':
            print("✅ Gemini API Key: Configured")
        else:
            print("⚠️  Gemini API Key: Not configured")
        
        if os.getenv('SLACK_WEBHOOK'):
            print("✅ Slack Webhook: Configured")
        
        if os.getenv('AWS_ACCESS_KEY_ID'):
            print("✅ AWS S3: Configured")
        
        print("\n" + "="*70)
        print("🎉 Setup Complete!")
        print("="*70)
        print("\nNext steps:")
        print("1. Review your .env file")
        print("2. Start the monitoring server:")
        print("   cd monitoring/server")
        print("   python app.py")
        print("3. Access dashboard at http://localhost:3001")
        print("4. Click 'Logs & AI Analysis' tab to use Gemini AI")
        print("\n" + "="*70)
        
    except ImportError:
        print("\n⚠️  python-dotenv not installed")
        print("Run: pip install python-dotenv")


def main():
    """Main setup function"""
    print_header()
    
    # Check if we're in the right directory
    if not Path("env.template").exists():
        print("❌ Error: Please run this script from the project root directory")
        print("   (where env.template is located)")
        sys.exit(1)
    
    # Check existing .env
    exists = check_existing_env()
    
    if not exists:
        # Create from template
        create_from_template()
    
    # Interactive configuration
    print("\n📝 Let's configure your environment variables...\n")
    config = configure_env()
    
    # Update .env file
    update_env_file(config)
    
    # Verify setup
    verify_setup()


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n⚠️  Setup cancelled by user")
        sys.exit(0)
    except Exception as e:
        print(f"\n❌ Error: {e}")
        sys.exit(1)

