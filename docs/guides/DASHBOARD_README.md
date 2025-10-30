# 🧠 ML Model Performance Dashboard

A real-time dashboard for monitoring your DDoS detection machine learning model performance and system statistics.

## 🚀 **QUICK START**

### **Windows:**
```cmd
start-dashboard.bat
```

### **Linux/Ubuntu:**
```bash
./start-dashboard.sh
```

### **Manual Docker:**
```bash
# Start only the dashboard
docker-compose up -d dashboard

# Or start the entire system
docker-compose up -d
```

## 🌐 **ACCESS POINTS**

- **📊 ML Dashboard**: http://localhost:3001
- **🤖 Model API**: http://localhost:8080
- **📈 Monitoring Server**: http://localhost:5000
- **📊 Prometheus**: http://localhost:9090
- **📊 Grafana**: http://localhost:3000

## ✨ **FEATURES**

### **Real-time ML Model Metrics**
- **Accuracy**: Model prediction accuracy percentage
- **Precision**: True positive rate for DDoS detection
- **Recall**: Sensitivity to actual DDoS attacks
- **F1 Score**: Harmonic mean of precision and recall
- **Prediction Time**: Average inference time in milliseconds
- **Throughput**: Predictions per second

### **System Performance Monitoring**
- **CPU Usage**: Real-time CPU utilization
- **Memory Usage**: RAM consumption tracking
- **Disk Usage**: Storage utilization
- **Network I/O**: Incoming and outgoing traffic

### **Attack Detection Statistics**
- **Total Detections**: Number of attacks detected
- **DDoS Attacks**: Confirmed DDoS incidents
- **False Positives**: Incorrect detections
- **Detection Rate**: Success rate percentage
- **Attack Types**: Distribution of attack types
- **Source IPs**: Top attacking IP addresses

### **Interactive Visualizations**
- **📈 Performance Charts**: Real-time ML metrics over time
- **🥧 Resource Usage**: System resource distribution
- **📊 Attack Distribution**: Attack types breakdown
- **📈 Throughput Trends**: Model performance trends

## 🎨 **DASHBOARD FEATURES**

### **Modern UI/UX**
- **Responsive Design**: Works on desktop, tablet, and mobile
- **Real-time Updates**: WebSocket-based live data streaming
- **Interactive Charts**: Chart.js powered visualizations
- **Status Indicators**: Live connection and health status
- **Bootstrap 5**: Modern, clean interface

### **Real-time Data**
- **WebSocket Connection**: Live data streaming every 2 seconds
- **Auto-reconnection**: Automatic reconnection on connection loss
- **Historical Data**: 100 data points for trend analysis
- **Performance Metrics**: Live ML model performance tracking

## 🔧 **TECHNICAL DETAILS**

### **Backend (FastAPI)**
- **Real-time Metrics Collection**: System and ML performance data
- **WebSocket Support**: Live data streaming to frontend
- **REST API**: Health checks and data endpoints
- **Background Tasks**: Continuous metrics collection
- **Docker Ready**: Containerized deployment

### **Frontend (HTML/CSS/JS)**
- **Chart.js**: Interactive charts and graphs
- **Bootstrap 5**: Responsive UI framework
- **Font Awesome**: Modern icons
- **WebSocket Client**: Real-time data consumption
- **Responsive Design**: Mobile-friendly interface

### **Data Sources**
- **ML Model API**: Direct integration with DDoS detection model
- **System Metrics**: CPU, memory, disk, network via psutil
- **Attack Statistics**: Simulated attack detection data
- **Historical Data**: Rolling window of 100 data points

## 📊 **MONITORING CAPABILITIES**

### **ML Model Performance**
- Track model accuracy, precision, recall, and F1 score
- Monitor prediction latency and throughput
- Visualize performance trends over time
- Alert on performance degradation

### **System Health**
- Real-time CPU, memory, and disk usage
- Network traffic monitoring
- Resource utilization trends
- System health indicators

### **Security Metrics**
- Attack detection statistics
- False positive/negative tracking
- Source IP analysis
- Attack type distribution
- Detection rate monitoring

## 🚀 **DEPLOYMENT**

### **Docker Compose**
The dashboard is included in the main docker-compose.yml:

```yaml
dashboard:
  build: ./monitoring/dashboard
  ports:
    - "3001:3001"
  depends_on:
    - model
```

### **Standalone Deployment**
```bash
# Build and run dashboard only
cd monitoring/dashboard
docker build -t ml-dashboard .
docker run -p 3001:3001 ml-dashboard
```

## 🔍 **API ENDPOINTS**

### **Health & Status**
- `GET /api/health` - Dashboard health check
- `GET /api/model/health` - ML model health status

### **Metrics**
- `GET /api/metrics/ml` - Current ML model metrics
- `GET /api/metrics/system` - Current system metrics
- `GET /api/metrics/attacks` - Attack detection statistics

### **Historical Data**
- `GET /api/history/ml` - ML metrics history
- `GET /api/history/system` - System metrics history

### **WebSocket**
- `WS /ws` - Real-time data streaming

## 🎯 **USE CASES**

### **ML Engineers**
- Monitor model performance in production
- Track accuracy and latency metrics
- Identify performance degradation
- Analyze prediction patterns

### **DevOps Teams**
- System resource monitoring
- Performance bottleneck identification
- Health status tracking
- Capacity planning

### **Security Teams**
- Attack detection monitoring
- Threat intelligence gathering
- False positive analysis
- Security incident tracking

## 🛠️ **CUSTOMIZATION**

### **Adding New Metrics**
1. Update `app.py` to collect new metrics
2. Add metric cards to `dashboard.html`
3. Update WebSocket data structure
4. Add charts for new visualizations

### **Modifying Charts**
- Edit chart configurations in `dashboard.html`
- Update Chart.js options
- Add new chart types as needed
- Customize colors and styling

### **API Extensions**
- Add new REST endpoints in `app.py`
- Implement new data collection methods
- Extend WebSocket message format
- Add authentication if needed

## 📈 **PERFORMANCE**

- **Update Frequency**: Every 2 seconds
- **Data Retention**: 100 data points (rolling window)
- **Memory Usage**: Minimal overhead
- **CPU Impact**: < 1% system resources
- **Network**: WebSocket for efficient real-time updates

## 🔒 **SECURITY**

- **No Authentication**: Currently open (add as needed)
- **Local Network**: Designed for internal monitoring
- **Data Privacy**: No external data transmission
- **Secure WebSocket**: WSS support available

## 🐛 **TROUBLESHOOTING**

### **Dashboard Not Loading**
```bash
# Check if dashboard is running
docker-compose ps dashboard

# Check logs
docker-compose logs dashboard

# Restart dashboard
docker-compose restart dashboard
```

### **No Data Showing**
```bash
# Check model service
docker-compose ps model

# Check model health
curl http://localhost:8080/health

# Check dashboard logs
docker-compose logs dashboard
```

### **WebSocket Connection Issues**
- Check firewall settings
- Verify port 3001 is accessible
- Check browser console for errors
- Ensure WebSocket support in browser

## 📝 **CHANGELOG**

### **v1.0.0**
- Initial dashboard release
- Real-time ML model monitoring
- System performance tracking
- Attack detection statistics
- Interactive visualizations
- WebSocket support
- Docker deployment ready

---

**🎉 Your ML Model Performance Dashboard is ready!**

Access it at: **http://localhost:3001**
