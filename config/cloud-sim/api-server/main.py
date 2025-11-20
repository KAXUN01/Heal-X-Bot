from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse
import psycopg2
import redis
import os
import time

app = FastAPI(title="Cloud Sim API Server")

# Database connection
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://postgres:postgres@database:5432/cloudsim")
REDIS_URL = os.getenv("REDIS_URL", "redis://cache:6379/0")

def get_db_connection():
    try:
        conn = psycopg2.connect(DATABASE_URL)
        return conn
    except Exception as e:
        return None

def get_redis_connection():
    try:
        r = redis.from_url(REDIS_URL)
        r.ping()
        return r
    except Exception as e:
        return None

@app.get("/health")
async def health():
    """Health check endpoint"""
    db_status = "connected" if get_db_connection() else "disconnected"
    redis_status = "connected" if get_redis_connection() else "disconnected"
    
    return {
        "status": "healthy",
        "service": "api-server",
        "database": db_status,
        "cache": redis_status,
        "timestamp": time.time()
    }

@app.get("/")
async def root():
    return {
        "service": "Cloud Simulation API Server",
        "status": "running",
        "port": 8000,
        "endpoints": ["/health", "/api/data"]
    }

@app.get("/api/data")
async def get_data():
    """Sample API endpoint"""
    return {
        "message": "Data from API server",
        "timestamp": time.time()
    }

@app.post("/api/data")
async def create_data(data: dict):
    """Sample POST endpoint"""
    return {
        "message": "Data created",
        "data": data,
        "timestamp": time.time()
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

