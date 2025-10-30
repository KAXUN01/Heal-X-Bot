# 🔑 How to Fix Gemini API Key Issue

## ❌ Current Problem

Your Gemini API key is not working. The system tested all available models and none were accessible with your current key.

## ✅ Solution: Get a New FREE API Key

### Step 1: Visit Google AI Studio
Open your browser and go to:
```
https://aistudio.google.com/app/apikey
```

### Step 2: Sign In
- Sign in with your Google account
- If you don't have one, create a free Google account first

### Step 3: Create API Key
1. Click the **"Create API Key"** button
2. Choose **"Create API key in new project"** (recommended)
3. Your new API key will be displayed

### Step 4: Copy the API Key
- Click the **copy icon** to copy your new API key
- It should look something like: `AIzaSyB...` (39 characters)

### Step 5: Update Your .env File

Open the `.env` file in your Healing-bot directory:
```bash
cd /home/cdrditgis/Documents/Healing-bot
nano .env
```

Find the line with `GEMINI_API_KEY` and replace it with your NEW key:
```env
GEMINI_API_KEY=AIzaSyB_your_actual_new_key_here
```

**Save and exit** (Ctrl+X, then Y, then Enter)

### Step 6: Restart the Monitoring Server

```bash
cd /home/cdrditgis/Documents/Healing-bot

# Stop the monitoring server
lsof -ti:5000 | xargs kill -9

# Restart it
source venv/bin/activate
cd monitoring/server
python app.py > ../../logs/monitoring-server.log 2>&1 &
```

### Step 7: Test the AI Analysis

Wait 5 seconds, then test:
```bash
curl http://localhost:5000/api/gemini/quick-analyze
```

You should see AI analysis results instead of error messages!

---

## 🧪 Verify Your New API Key

You can test if your new API key works by running:
```bash
cd /home/cdrditgis/Documents/Healing-bot
source venv/bin/activate
python test_gemini_models.py
```

This will show you which models are available with your new key.

---

## 💡 Important Notes

1. **Free Tier**: Google's Gemini API has a generous free tier
2. **Rate Limits**: Free tier has rate limits (15 requests per minute)
3. **Valid Format**: API keys start with `AIza` and are exactly 39 characters
4. **Keep it Secret**: Never share your API key publicly or commit it to git

---

## ⚠️ System Works WITHOUT AI Analysis

**Good News**: Your Healing-bot system is fully functional even without the Gemini API key!

**Working Features (No API Key Needed)**:
- ✅ Centralized log collection
- ✅ Real-time anomaly detection  
- ✅ Critical issue tracking
- ✅ Network monitoring
- ✅ DDoS detection
- ✅ IP blocking
- ✅ Dashboard visualization

**AI Features (Requires Valid API Key)**:
- 🤖 Intelligent log analysis
- 🤖 Error explainability
- 🤖 Root cause suggestions
- 🤖 Smart recommendations

---

## 🆘 Still Having Issues?

If you continue to have problems after getting a new API key:

1. **Check the key format**: Should be 39 characters starting with `AIza`
2. **Verify it's in .env**: Make sure there are no extra spaces or quotes
3. **Restart the server**: Always restart after changing the .env file
4. **Check logs**: `tail -f logs/monitoring-server.log`

---

## 📞 Alternative: Disable AI Features

If you want to run the system without AI analysis:

The system will automatically detect an invalid API key and show helpful messages instead of errors. The "Analyze" button will display instructions on how to enable AI features when clicked.

All other features will continue to work perfectly!

---

**Generated**: October 29, 2025
**Last Updated**: After API key testing

