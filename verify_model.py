
import os
import sys
from pathlib import Path
from dotenv import load_dotenv

# Load env variables
env_path = Path(os.getcwd()) / '.env'
print(f"Loading .env from {env_path}")
load_dotenv(dotenv_path=env_path)

# Add server directory to path
sys.path.append(os.path.join(os.getcwd(), 'monitoring/server'))

from gemini_log_analyzer import GeminiLogAnalyzer

def verify_model():
    print("Initializing GeminiLogAnalyzer...")
    try:
        analyzer = GeminiLogAnalyzer()
        
        if analyzer.model:
            print(f"✅ Success! Initialized with model: {analyzer.model_name}")
            
            # Check if it matches our expectation
            expected = "gemini-1.5-pro"
            if analyzer.model_name == expected:
                print(f"✅ Verified: Model is correctly set to {expected}")
            else:
                print(f"⚠️ Warning: Model is {analyzer.model_name}, expected {expected}")
                
            # Try a simple analysis to ensure it works
            print("\nTesting analysis capability...")
            result = analyzer.analyze_error_log({
                "service": "test-service",
                "message": "Connection refused to database",
                "timestamp": "2023-01-01T00:00:00"
            })
            
            if result.get('status') == 'success':
                print("✅ Analysis successful")
                print("Analysis Output Snippet:")
                print(result['analysis']['full_analysis'][:100] + "...")
            else:
                print(f"❌ Analysis failed: {result.get('message')}")
                
        else:
            print("❌ Failed to initialize model (model is None)")
            
    except Exception as e:
        print(f"❌ Error during verification: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    verify_model()
