# Groq API Fallback Implementation

## Overview
Implemented automatic runtime fallback from Gemini to Groq API when Gemini fails during log analysis operations.

## Changes Made

### 1. Enhanced API Endpoints with Runtime Fallback

Modified three API endpoints in `monitoring/server/healing_dashboard_api.py`:

#### a) `/api/gemini/analyze-log` (Line 4166)
- **Purpose**: Analyze single log entries
- **Fallback Logic**: If Gemini analysis fails, automatically switches to Groq
- **Benefits**: Ensures log analysis continues even if Gemini API is down

#### b) `/api/gemini/analyze-pattern` (Line 4237)
- **Purpose**: Analyze multiple logs for patterns
- **Fallback Logic**: Same automatic Groq fallback on Gemini failure
- **Benefits**: Pattern detection remains operational during Gemini outages

#### c) `/api/gemini/analyze-service/{service_name}` (Line 4301)
- **Purpose**: Analyze overall service health
- **Fallback Logic**: Automatic Groq fallback for service health analysis
- **Benefits**: Service monitoring continues uninterrupted

### 2. Fallback Mechanism Details

```python
# Try primary analyzer (Gemini)
try:
    analysis = _ai_analyzer.analyze_error_log(log_entry)
    return analysis
except Exception as primary_error:
    # Automatic fallback to Groq
    if _analyzer_type == 'gemini':
        groq_key = os.getenv('GROQ_API_KEY')
        if groq_key and GROQ_AVAILABLE:
            # Initialize and switch to Groq
            initialize_groq_analyzer(api_key=groq_key)
            _ai_analyzer = groq_analyzer
            _analyzer_type = 'groq'
            
            # Retry with Groq
            analysis = _ai_analyzer.analyze_error_log(log_entry)
            return analysis
```

### 3. Logging and Monitoring

The implementation includes comprehensive logging:
- `🔄 Attempting fallback to Groq analyzer...` - When fallback starts
- `✅ Successfully switched to Groq analyzer` - When fallback succeeds
- `Groq fallback failed: {error}` - When fallback fails
- `No Groq API key available for fallback` - When Groq key is missing

## Configuration Required

Ensure both API keys are set in `.env` file:

```env
# Primary AI Provider (Gemini)
GEMINI_API_KEY=your_gemini_api_key_here

# Fallback AI Provider (Groq)
GROQ_API_KEY=your_groq_api_key_here
```

## How It Works

### Initialization (Startup)
1. System tries to initialize Gemini first
2. If Gemini fails, falls back to Groq during startup
3. Logs which analyzer is active

### Runtime (During Analysis)
1. Uses current analyzer (Gemini by default)
2. If analysis fails:
   - Checks if current analyzer is Gemini
   - Verifies GROQ_API_KEY is available
   - Initializes Groq analyzer
   - Switches global analyzer to Groq
   - Retries the analysis operation
3. All subsequent requests use Groq until service restart

## Benefits

1. **High Availability**: Log analysis continues even if primary API fails
2. **Automatic Recovery**: No manual intervention required
3. **Transparent**: Users don't notice the switch
4. **Cost Optimization**: Uses free/cheaper Groq when Gemini is unavailable
5. **Resilience**: System remains operational during API outages

## Testing

To test the fallback mechanism:

1. **Simulate Gemini Failure**:
   - Set invalid GEMINI_API_KEY
   - Or remove GEMINI_API_KEY temporarily
   - System should automatically use Groq

2. **Monitor Logs**:
   ```bash
   tail -f /var/log/heal-x/heal-x.log | grep -E "(Gemini|Groq|fallback)"
   ```

3. **Verify Dashboard**:
   - Go to Logs & AI tab
   - Click "Analyze" on any error log
   - Check console for fallback messages

## Notes

- Once switched to Groq, the system stays on Groq until restart
- This is intentional to avoid repeated API failures
- To switch back to Gemini, restart the dashboard service:
  ```bash
  sudo systemctl restart heal-x-dashboard
  ```

## Future Enhancements

Potential improvements:
1. Add retry logic before fallback (e.g., retry Gemini 2-3 times)
2. Implement periodic health checks to switch back to Gemini
3. Add metrics to track fallback frequency
4. Support additional AI providers (Claude, OpenAI, etc.)
5. Add user preference for primary AI provider

## Related Files

- `monitoring/server/healing_dashboard_api.py` - API endpoints with fallback logic
- `ai/gemini_log_analyzer.py` - Gemini analyzer implementation
- `ai/groq_log_analyzer.py` - Groq analyzer implementation
- `docs/features/AI_LOG_ANALYSIS.md` - AI analysis documentation
