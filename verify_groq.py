
import os
import sys
from pathlib import Path
from dotenv import load_dotenv

# Load env variables
env_path = Path(os.getcwd()) / '.env'
print(f"Loading .env from {env_path}")
load_dotenv(dotenv_path=env_path)

# Verify API key
groq_key = os.getenv('GROQ_API_KEY')
if not groq_key:
    print("❌ Error: GROQ_API_KEY not found in environment!")
    sys.exit(1)
else:
    print(f"✅ GROQ_API_KEY found ({groq_key[:5]}...)")

# Add server directory to path
sys.path.append(os.path.join(os.getcwd(), 'monitoring/server'))

from groq_log_analyzer import GroqLogAnalyzer

def verify_groq():
    print("Initializing GroqLogAnalyzer...")
    try:
        analyzer = GroqLogAnalyzer()
        
        if analyzer.client:
            print(f"✅ Success! Initialized Groq client")
            print(f"✅ Model: {analyzer.model_name}")
            
            # Check if it matches our expectation
            expected = "llama-3.3-70b-versatile"
            if analyzer.model_name == expected:
                print(f"✅ Verified: Model is correctly set to {expected}")
            else:
                print(f"⚠️ Warning: Model is {analyzer.model_name}, expected {expected}")
                
            # Try a simple analysis to ensure it works
            print("\nTesting Groq analysis capability...")
            result = analyzer.analyze_error_log({
                "service": "test-service",
                "message": "Connection refused to database",
                "timestamp": "2023-01-01T00:00:00"
            })
            
            if result.get('status') == 'success':
                print("✅ Groq Analysis successful")
                print("Analysis Output Snippet:")
                print(result['analysis']['full_analysis'][:100] + "...")
            else:
                print(f"❌ Groq Analysis failed: {result.get('message')}")
                if 'analysis' in result:
                    print(f"Details: {result['analysis']}")
                
        else:
            print("❌ Failed to initialize Groq client")
            
    except Exception as e:
        print(f"❌ Error during verification: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    verify_groq()
