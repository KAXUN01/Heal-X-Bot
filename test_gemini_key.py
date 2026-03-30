#!/usr/bin/env python3
"""
Test script to verify Gemini API key configuration
"""
import os
import sys
from pathlib import Path
from dotenv import load_dotenv

# Load .env file
env_path = Path(__file__).parent / '.env'
load_dotenv(dotenv_path=env_path, override=True)

# Check API key
api_key = os.getenv('GEMINI_API_KEY') or os.getenv('GOOGLE_API_KEY')

print("=" * 60)
print("Gemini API Key Configuration Test")
print("=" * 60)
print()

if not api_key:
    print("❌ ERROR: GEMINI_API_KEY not found in .env file")
    print()
    print("Please add your API key to .env file:")
    print("  GEMINI_API_KEY=your_actual_api_key_here")
    sys.exit(1)

if api_key == "your_gemini_api_key_here":
    print("❌ ERROR: API key is still set to placeholder value")
    print()
    print("Please replace 'your_gemini_api_key_here' with your actual API key")
    sys.exit(1)

if len(api_key) < 20:
    print(f"❌ ERROR: API key is too short ({len(api_key)} characters)")
    print("   Valid Gemini API keys are at least 20 characters")
    sys.exit(1)

if not api_key.startswith('AIza'):
    print(f"⚠️  WARNING: API key doesn't start with 'AIza'")
    print(f"   First 10 chars: {api_key[:10]}")
    print("   This might still be valid, but most Gemini keys start with 'AIza'")
    print()

print(f"✅ API key found in .env file")
print(f"   Length: {len(api_key)} characters")
print(f"   Starts with AIza: {api_key.startswith('AIza')}")
print(f"   First 10 chars: {api_key[:10]}...")
print()

# Try to initialize the analyzer
print("Testing Gemini analyzer initialization...")
try:
    sys.path.insert(0, str(Path(__file__).parent / 'monitoring' / 'server'))
    from gemini_log_analyzer import initialize_gemini_analyzer, gemini_analyzer
    
    analyzer = initialize_gemini_analyzer(api_key=api_key)
    
    if analyzer and analyzer.api_key:
        print(f"✅ Analyzer initialized with API key")
        print(f"   API key length in analyzer: {len(analyzer.api_key)}")
        
        if analyzer.model:
            print(f"✅ Gemini model initialized successfully")
            print(f"   Model name: {analyzer.model_name}")
            print()
            print("🎉 SUCCESS! Your Gemini API key is configured correctly!")
            print()
            print("Next steps:")
            print("1. Restart your monitoring server:")
            print("   - If using healing_dashboard_api.py:")
            print("     pkill -f healing_dashboard_api")
            print("     python3 monitoring/server/healing_dashboard_api.py")
            print("   - If using app.py:")
            print("     pkill -f 'monitoring/server/app.py'")
            print("     python3 monitoring/server/app.py")
            print()
            print("2. After restart, try the AI analysis feature again")
        else:
            print("⚠️  Analyzer initialized but model not available")
            print("   This might indicate an invalid API key or network issue")
            print("   Try testing the API key at: https://aistudio.google.com/")
    else:
        print("❌ Analyzer initialized but API key is missing")
        print("   This shouldn't happen - please check the code")
        
except ImportError as e:
    print(f"❌ ERROR: Could not import gemini_log_analyzer: {e}")
    print("   Make sure you're in the project root directory")
    sys.exit(1)
except Exception as e:
    print(f"❌ ERROR: Failed to initialize analyzer: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

print()
print("=" * 60)

