from motor.motor_asyncio import AsyncIOMotorClient
import asyncio
from datetime import datetime

# MongoDB connection URI
MONGO_URI = "mongodb+srv://dankmater404:admin123@cluster0.9pq3hla.mongodb.net/Cluster0?retryWrites=true&w=majority&appName=Cluster0"

# MongoDB client
client = AsyncIOMotorClient(MONGO_URI)
db = client.Cluster0
logs_collection = db.logs  # Assuming the logs are stored in a collection named "logs"

# Sample test log data
test_logs = [
    {
        "timestamp": datetime.now().isoformat(),
        "ipAddress": "192.168.1.1",
        "userAgent": "Mozilla/5.0",
        "geoLocation": "New York, USA",
        "httpHeaders": '{"User-Agent": "Mozilla/5.0"}',
        "urlPath": "/home",
        "queryParameters": '{"search": "fastapi"}',
        "connectionDuration": "123ms",
        "referrer": "https://google.com",
        "cookies": '{"session_id": "abc123"}',
        "protocolType": "HTTP/1.1",
        "portNumber": "8080",
        "trafficVolume": 1024,
        "sessionId": "abc123",
        "requestMethod": "GET",
        "responseTime": 123,
        "statusCode": 200,
        "requestPayloadSize": 0,
    },
    {
        "timestamp": datetime.now().isoformat(),
        "ipAddress": "192.168.1.2",
        "userAgent": "Mozilla/5.0",
        "geoLocation": "London, UK",
        "httpHeaders": '{"User-Agent": "Mozilla/5.0"}',
        "urlPath": "/login",
        "queryParameters": '{"username": "test"}',
        "connectionDuration": "150ms",
        "referrer": "https://bing.com",
        "cookies": '{"session_id": "xyz456"}',
        "protocolType": "HTTP/2",
        "portNumber": "443",
        "trafficVolume": 2048,
        "sessionId": "xyz456",
        "requestMethod": "POST",
        "responseTime": 150,
        "statusCode": 201,
        "requestPayloadSize": 100,
    }
]

async def insert_test_logs():
    # Insert multiple test logs
    result = await logs_collection.insert_many(test_logs)
    print(f"Inserted {len(result.inserted_ids)} test logs.")

# Run the script to insert the test logs
asyncio.run(insert_test_logs())
