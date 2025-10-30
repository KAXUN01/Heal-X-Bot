#!/usr/bin/env python3
"""Test which Gemini models are available with the current API key"""

import os
import requests
from dotenv import load_dotenv

# Load environment
load_dotenv()

api_key = os.getenv('GEMINI_API_KEY') or os.getenv('GOOGLE_API_KEY')

if not api_key:
    print("❌ No API key found in environment")
    exit(1)

print(f"🔑 API Key found (length: {len(api_key)})")
print()

# List of models to test
models_to_test = [
    "gemini-pro",
    "gemini-1.5-pro",
    "gemini-1.5-flash",
    "gemini-1.5-flash-latest",
    "gemini-1.0-pro"
]

print("🧪 Testing available Gemini models...")
print()

available_models = []

for model in models_to_test:
    # Try v1beta first
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent"
    
    payload = {
        "contents": [{
            "parts": [{
                "text": "Hello"
            }]
        }]
    }
    
    try:
        response = requests.post(
            url,
            json=payload,
            params={"key": api_key},
            timeout=5
        )
        
        if response.status_code == 200:
            print(f"✅ {model} - AVAILABLE (v1beta)")
            available_models.append((model, "v1beta"))
        elif response.status_code == 404:
            # Try v1 API
            url_v1 = f"https://generativelanguage.googleapis.com/v1/models/{model}:generateContent"
            response_v1 = requests.post(
                url_v1,
                json=payload,
                params={"key": api_key},
                timeout=5
            )
            if response_v1.status_code == 200:
                print(f"✅ {model} - AVAILABLE (v1)")
                available_models.append((model, "v1"))
            else:
                print(f"❌ {model} - Not available")
        else:
            print(f"⚠️  {model} - Error {response.status_code}")
            
    except Exception as e:
        print(f"❌ {model} - Error: {str(e)[:50]}")

print()
print("=" * 70)
if available_models:
    print(f"✅ Found {len(available_models)} available model(s):")
    for model, version in available_models:
        print(f"   • {model} ({version})")
    print()
    print(f"📝 Recommended: Use '{available_models[0][0]}' with API version '{available_models[0][1]}'")
else:
    print("❌ No models available. Check your API key permissions.")
    print("   Get a new key: https://makersuite.google.com/app/apikey")
print("=" * 70)

