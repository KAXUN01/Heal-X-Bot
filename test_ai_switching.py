#!/usr/bin/env python3
"""
Test script to verify AI analyzer switching logic
"""

import os
import sys
from pathlib import Path
from dotenv import load_dotenv

# Load environment
env_path = Path(__file__).parent / '.env'
load_dotenv(dotenv_path=env_path)

print("="*60)
print("AI Analyzer Switching Test")
print("="*60)

# Check which keys are available
gemini_key = os.getenv('GEMINI_API_KEY') or os.getenv('GOOGLE_API_KEY')
groq_key = os.getenv('GROQ_API_KEY')

print(f"\n✅ GEMINI_API_KEY found: {bool(gemini_key)}")
if gemini_key:
    print(f"   Length: {len(gemini_key)} characters")
    print(f"   Starts with 'AIza': {gemini_key.startswith('AIza')}")

print(f"\n✅ GROQ_API_KEY found: {bool(groq_key)}")
if groq_key:
    print(f"   Length: {len(groq_key)} characters")

# Test imports
print("\n" + "="*60)
print("Testing Analyzer Imports")
print("="*60)

gemini_available = False
groq_available = False

try:
    from monitoring.server.gemini_log_analyzer import GeminiLogAnalyzer
    gemini_available = True
    print("\n✅ GeminiLogAnalyzer imported successfully")
except ImportError as e:
    print(f"\n❌ GeminiLogAnalyzer import failed: {e}")

try:
    sys.path.insert(0, str(Path(__file__).parent / 'monitoring' / 'server'))
    from groq_log_analyzer import GroqLogAnalyzer
    groq_available = True
    print("✅ GroqLogAnalyzer imported successfully")
except ImportError as e:
    print(f"❌ GroqLogAnalyzer import failed: {e}")

# Test initialization
print("\n" + "="*60)
print("Testing Analyzer Initialization")
print("="*60)

if gemini_key and gemini_available:
    try:
        analyzer = GeminiLogAnalyzer(api_key=gemini_key)
        if analyzer and analyzer.model:
            print(f"\n✅ Gemini analyzer initialized successfully!")
            print(f"   Model: {analyzer.model_name}")
        else:
            print("\n⚠️  Gemini analyzer created but model not initialized")
    except Exception as e:
        print(f"\n❌ Gemini analyzer initialization failed: {e}")
elif gemini_key:
    print("\n⚠️  GEMINI_API_KEY found but module not available")
else:
    print("\n⚠️  No GEMINI_API_KEY found")

if groq_key and groq_available:
    try:
        analyzer = GroqLogAnalyzer(api_key=groq_key)
        if analyzer and analyzer.client:
            print(f"\n✅ Groq analyzer initialized successfully!")
            print(f"   Model: {analyzer.model_name}")
        else:
            print("\n⚠️  Groq analyzer created but client not initialized")
    except Exception as e:
        print(f"\n❌ Groq analyzer initialization failed: {e}")
elif groq_key:
    print("\n⚠️  GROQ_API_KEY found but module not available")
else:
    print("\n⚠️  No GROQ_API_KEY found")

print("\n" + "="*60)
print("Test Complete")
print("="*60)
