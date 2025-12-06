#!/bin/bash
echo "Checking Gemini API key configuration..."
python3 -c "
from pathlib import Path
from dotenv import load_dotenv
import os

env_path = Path('.env')
if env_path.exists():
    load_dotenv(dotenv_path=env_path, override=True)
    api_key = os.getenv('GEMINI_API_KEY') or os.getenv('GOOGLE_API_KEY')
    if api_key:
        print(f'✅ API key found in .env file')
        print(f'   Length: {len(api_key)} characters')
        print(f'   Starts with AIza: {api_key.startswith(\"AIza\")}')
        print(f'   First 10 chars: {api_key[:10]}...')
    else:
        print('❌ API key not found in .env file')
        print('   Please add GEMINI_API_KEY=your_key_here to .env file')
else:
    print('❌ .env file not found')
    print('   Please create .env file in project root')
"
