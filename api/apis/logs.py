from fastapi import FastAPI, HTTPException
from motor.motor_asyncio import AsyncIOMotorClient
from typing import List
from pydantic import BaseModel

# MongoDB connection URI
MONGO_URI = "mongodb+srv://dankmater404:admin123@cluster0.9pq3hla.mongodb.net/Cluster0?retryWrites=true&w=majority&appName=Cluster0"

# FastAPI instance
app = FastAPI()

# MongoDB client
client = AsyncIOMotorClient(MONGO_URI)
db = client.Cluster0
logs_collection = db.logs  # Assuming the logs are stored in a collection named "logs"

# Pydantic Model for the log
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

@app.get("/logs", response_model=List[Log])
async def get_logs():
    """
    Retrieve all logs from MongoDB.
    """
    logs = await logs_collection.find().to_list(1000)  # Fetch up to 1000 logs
    if not logs:
        raise HTTPException(status_code=404, detail="No logs found")
    
    return logs

# Run the server using the following command:
# uvicorn main:app --reload
