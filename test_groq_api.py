"""
Quick test script to verify Groq API key is working
"""
import os
import sys

# Load .env file
from pathlib import Path
env_file = Path(__file__).parent / '.env'
if env_file.exists():
    with open(env_file) as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith('#') and '=' in line:
                key, value = line.split('=', 1)
                os.environ[key.strip()] = value.strip()

api_key = os.getenv('GROQ_API_KEY')

print("=" * 60)
print("GROQ API KEY VERIFICATION")
print("=" * 60)

if not api_key:
    print("❌ ERROR: GROQ_API_KEY not found in .env file")
    sys.exit(1)

print(f"✓ API Key found")
print(f"  Length: {len(api_key)} characters")
print(f"  Starts with: {api_key[:10]}...")
print(f"  Ends with: ...{api_key[-10:]}")

# Check format
if not api_key.startswith('gsk_'):
    print("⚠️ WARNING: Groq API keys typically start with 'gsk_'")

if len(api_key) < 40:
    print("⚠️ WARNING: API key seems too short")

print("\n[Testing API connection...]")

try:
    from groq import Groq
    
    client = Groq(api_key=api_key)
    
    # Make a simple test call
    response = client.chat.completions.create(
        model="llama-3.1-8b-instant",
        messages=[{"role": "user", "content": "Say 'API working' in 2 words"}],
        max_tokens=10,
        temperature=0
    )
    
    result = response.choices[0].message.content
    print(f"✅ SUCCESS! API Response: {result}")
    print("\nYour Groq API key is working correctly!")
    
except ImportError:
    print("❌ ERROR: 'groq' package not installed")
    print("   Run: pip install groq")
except Exception as e:
    error_msg = str(e)
    print(f"❌ API ERROR: {error_msg}")
    
    if "401" in error_msg or "authentication" in error_msg.lower():
        print("\n🔑 Your API key is INVALID or EXPIRED")
        print("   Get a new key from: https://console.groq.com/keys")
    elif "429" in error_msg:
        print("\n⏱️ Rate limited - too many requests")
    elif "connection" in error_msg.lower() or "network" in error_msg.lower():
        print("\n🌐 Network error - check your internet connection")
