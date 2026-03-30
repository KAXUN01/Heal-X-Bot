
import os
import sys
from pathlib import Path
from dotenv import load_dotenv

# Load env variables
env_path = Path(os.getcwd()) / '.env'
load_dotenv(dotenv_path=env_path)

# Verify API key
groq_key = os.getenv('GROQ_API_KEY')
if not groq_key:
    print("❌ Error: GROQ_API_KEY not found in environment!")
    sys.exit(1)

# Add server directory to path
sys.path.append(os.path.join(os.getcwd(), 'monitoring/server'))

from groq_log_analyzer import GroqLogAnalyzer

def verify_conciseness():
    print("Initializing GroqLogAnalyzer...")
    try:
        analyzer = GroqLogAnalyzer()
        
        print("\nTesting Groq analysis capability (expecting concise output)...")
        result = analyzer.analyze_cloud_fault({
            "type": "service_crash",
            "service": "test-service",
            "status": "exited",
            "restart_count": 5,
            "timestamp": "2023-01-01T00:00:00"
        })
        
        if result.get('status') == 'success':
            print("✅ Groq Analysis successful")
            analysis = result['analysis']
            
            root_cause = analysis.get('root_cause', '')
            solution = analysis.get('solution', '')
            prevention = analysis.get('prevention', '')
            why = analysis.get('why') # Should be None or not present in key logic
            
            print(f"\nRoot Cause ({len(root_cause)} chars): {root_cause}")
            print(f"Solution ({len(solution)} chars): {solution}")
            print(f"Prevention ({len(prevention)} chars): {prevention}")
            
            if why:
                 print(f"Why field: {why}")
            else:
                 print("✅ 'Why' field correctly removed/hidden from this view logic (though analyze_cloud_fault might return it if not updated properly, checking keys...)")
                 
            # Note: analyze_cloud_fault dict keys were updated in the file edit
            if 'why' not in analysis:
                print("✅ 'why' key is ABSENT from response (Good!)")
            else:
                print(f"⚠️ 'why' key is PRESENT: {analysis['why']}")

            # Check length constraints (heuristic)
            if len(root_cause) > 500: # 500 chars is generous for 2 sentences, but if it's 2000+ it's bad
                print("❌ Root cause seems too long!")
            else:
                print("✅ Root cause length seems concise.")
                
        else:
            print(f"❌ Groq Analysis failed: {result.get('message')}")
            
    except Exception as e:
        print(f"❌ Error during verification: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    verify_conciseness()
