@echo off
echo Starting Healing-bot components...

echo Starting Model API...
start "Model API" cmd /k "cd model && python main.py"

echo Starting Network Analyzer...
start "Network Analyzer" cmd /k "cd monitoring/server && python network_analyzer.py"

echo Starting Dashboard...
start "Dashboard" cmd /k "cd monitoring/dashboard && python app.py"

echo Starting Incident Bot...
start "Incident Bot" cmd /k "cd incident-bot && python main.py"

echo All components started!
echo.
echo Access points:
echo - Dashboard: http://localhost:3001
echo - Model API: http://localhost:8080
echo - Network Analyzer: http://localhost:8000
echo - Incident Bot: http://localhost:8000
echo.
pause
