from google import genai
import os
from dotenv import load_dotenv

# Load environment variables from .env
load_dotenv()

# Get API key from environment
api_key = os.getenv('GEMINI_API_KEY') or os.getenv('GOOGLE_API_KEY')

if not api_key:
    print("❌ No API key found in environment")
    print("Make sure GEMINI_API_KEY is set in your .env file")
    exit(1)

print(f"🔑 Using API key: {api_key[:10]}...")
print(f"🧪 Testing Gemini API with gemini-2.5-flash model...")
print()

# Create client with API key
client = genai.Client(api_key=api_key)

try:
    response = client.models.generate_content(
        model="gemini-2.5-flash", contents="Explain how AI works in a few words"
    )
    print("✅ SUCCESS! Gemini API is working!")
    print()
    print("Response from AI:")
    print("=" * 70)
    print(response.text)
    print("=" * 70)
except Exception as e:
    print(f"❌ ERROR: {e}")
    print()
    print("This could mean:")
    print("  • API key is invalid or expired")
    print("  • Model 'gemini-2.5-flash' not available with your key")
    print("  • API access issues")
    print()
    print("Get a new API key: https://aistudio.google.com/app/apikey")
