from fastapi import FastAPI
from pydantic import BaseModel
import os
import asyncio
from motor.motor_asyncio import AsyncIOMotorClient
import subprocess
import re
import psutil
from datetime import datetime

# MongoDB connection URI
MONGO_URI = 'mongodb+srv://dankmater404:admin123@cluster0.9pq3hla.mongodb.net/Cluster0?retryWrites=true&w=majority&appName=Cluster0'
client = AsyncIOMotorClient(MONGO_URI)
db = client.Cluster0
system_health_collection = db.system_health

# FastAPI instance
app = FastAPI()

# Pydantic model for response
class HealthResponse(BaseModel):
    status: str
    details: str

class SpeedResponse(BaseModel):
    traffic_in: int
    traffic_out: int

class TimeResponse(BaseModel):
    uptime: float
    downtime: float

def get_system_uptime() -> float:
    # System boot time in seconds since the epoch
    boot_time_timestamp = psutil.boot_time()
    boot_time = datetime.fromtimestamp(boot_time_timestamp)
    # Calculate uptime in seconds
    uptime_seconds = (datetime.now() - boot_time).total_seconds()
    return uptime_seconds

# Function to get system downtime (we assume system downtime is zero if it hasn't restarted)
def get_system_downtime() -> float:
    # This is not typically tracked on modern systems unless managed externally.
    # We'll return 0 assuming the system hasn't been down since the last boot.
    return 0


# Network traffic (in and out)
async def get_network_traffic() -> dict:
    try:
        command_output = subprocess.check_output('cat /proc/net/dev', shell=True).decode('utf-8')
        lines = command_output.split('\n')[2:]  # Skip the first two lines

        traffic_in = 0
        traffic_out = 0

        for line in lines:
            columns = re.split(r'\s+', line.strip())
            if len(columns) >= 10:
                traffic_in += int(columns[1])   # Bytes received
                traffic_out += int(columns[9])  # Bytes transmitted

        return {"traffic_in": traffic_in, "traffic_out": traffic_out}
    except Exception as e:
        print(f"Error getting network traffic: {e}")
        return {"traffic_in": 0, "traffic_out": 0}

# Health check by pinging Google's DNS (8.8.8.8)
async def perform_health_check() -> dict:
    try:
        command_output = subprocess.check_output('ping -c 1 8.8.8.8', shell=True).decode('utf-8')
        return {"status": "Healthy", "details": command_output}
    except subprocess.CalledProcessError as e:
        return {"status": "Unhealthy", "details": str(e)}

# Route to check system health
@app.get("/health", response_model=HealthResponse)
async def health_check():
    health = await perform_health_check()
    return HealthResponse(status=health["status"], details=health["details"])

# Route to check network traffic speed
@app.get("/speed", response_model=SpeedResponse)
async def network_speed():
    traffic = await get_network_traffic()
    return SpeedResponse(traffic_in=traffic["traffic_in"], traffic_out=traffic["traffic_out"])

# Route to check system uptime and downtime
@app.get("/time", response_model=TimeResponse)
async def uptime_downtime():
    uptime = get_system_uptime()
    downtime = get_system_downtime()
    return TimeResponse(uptime=uptime, downtime=downtime)

# Save system health data to MongoDB
async def log_system_health():
    uptime = get_system_uptime()
    downtime = get_system_downtime()
    traffic = await get_network_traffic()
    health = await perform_health_check()

    health_entry = {
        "systemUptime": uptime,
        "systemDowntime": downtime,
        "networkTrafficIn": traffic["traffic_in"],
        "networkTrafficOut": traffic["traffic_out"],
        "healthCheckStatus": health["status"],
        "healthCheckDetails": health["details"]
    }

    try:
        await system_health_collection.insert_one(health_entry)
        print("System health data logged to MongoDB")
    except Exception as e:
        print(f"Error logging system health data to MongoDB: {e}")

# Periodically log system health data (e.g., every 5 minutes)
async def log_health_periodically():
    while True:
        await log_system_health()
        await asyncio.sleep(5 * 60)  # Log every 5 minutes

@app.on_event("startup")
async def startup_event():
    asyncio.create_task(log_health_periodically())
