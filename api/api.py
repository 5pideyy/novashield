from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import os
import asyncio
from motor.motor_asyncio import AsyncIOMotorClient
import subprocess
import re
import psutil
from datetime import datetime
from typing import List, Dict

# MongoDB connection URI
MONGO_URI = "mongodb+srv://dankmater404:admin123@cluster0.9pq3hla.mongodb.net/Cluster0?retryWrites=true&w=majority&appName=Cluster0"

# MongoDB client
client = AsyncIOMotorClient(MONGO_URI)
db = client.Cluster0
system_health_collection = db.system_health  # Collection for system health logs
logs_collection = db.logs  # Collection for logs
blocked_requests_collection = db.blocked_requests  # Collection for blocked requests

# FastAPI instance
app = FastAPI()

# Pydantic models for responses
class HealthResponse(BaseModel):
    status: str
    details: str

class SpeedResponse(BaseModel):
    traffic_in: int
    traffic_out: int

class TimeResponse(BaseModel):
    uptime: float
    downtime: float

class Log(BaseModel):
    timestamp: str
    ipAddress: str
    userAgent: str
    geoLocation: str
    httpHeaders: str
    urlPath: str
    queryParameters: str
    connectionDuration: str
    referrer: str
    cookies: str
    protocolType: str
    portNumber: str
    trafficVolume: int
    sessionId: str
    requestMethod: str
    responseTime: int
    statusCode: int
    requestPayloadSize: int

class TopResponse(BaseModel):
    total_requests: int
    blocked_requests: int
    server_usage: Dict[str, float]
    blocked_ips: List[str]

class GraphDataResponse(BaseModel):
    total_requests: int
    blocked_requests: int

# System uptime and downtime
def get_system_uptime() -> float:
    # System boot time in seconds since the epoch
    boot_time_timestamp = psutil.boot_time()
    boot_time = datetime.fromtimestamp(boot_time_timestamp)
    # Calculate uptime in seconds
    uptime_seconds = (datetime.now() - boot_time).total_seconds()
    return uptime_seconds

def get_system_downtime() -> float:
    # Downtime is assumed to be zero if the system hasn't restarted
    return 0

# Get server usage (CPU and Memory)
def get_server_usage() -> Dict[str, float]:
    cpu_usage = psutil.cpu_percent(interval=1)
    memory_usage = psutil.virtual_memory().percent
    return {"cpu_usage": cpu_usage, "memory_usage": memory_usage}

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

# Periodically log system health data
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

# Periodically log system health data every 5 minutes
async def log_health_periodically():
    while True:
        await log_system_health()
        await asyncio.sleep(5 * 60)  # Log every 5 minutes

@app.on_event("startup")
async def startup_event():
    asyncio.create_task(log_health_periodically())

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

# Route to retrieve all logs
@app.get("/logs", response_model=List[Log])
async def get_logs():
    logs = await logs_collection.find().to_list(1000)  # Fetch up to 1000 logs
    if not logs:
        raise HTTPException(status_code=404, detail="No logs found")
    return logs

# API 1: /top - Summary with total requests, blocked requests, server usage, and blocked IPs
@app.get("/top", response_model=TopResponse)
async def get_top_summary():
    total_requests = await logs_collection.count_documents({})
    blocked_requests = await blocked_requests_collection.count_documents({})
    blocked_ips = await blocked_requests_collection.distinct("ipAddress")
    server_usage = get_server_usage()
    return TopResponse(
        total_requests=total_requests,
        blocked_requests=blocked_requests,
        server_usage=server_usage,
        blocked_ips=blocked_ips
    )

# API 2: /graph - Data for plotting total and blocked requests
@app.get("/graph", response_model=GraphDataResponse)
async def get_graph_data():
    total_requests = await logs_collection.count_documents({})
    blocked_requests = await blocked_requests_collection.count_documents({})
    return GraphDataResponse(
        total_requests=total_requests,
        blocked_requests=blocked_requests
    )
