import mongoose from 'mongoose';
import os from 'os';
import { exec } from 'child_process';
import geoip from 'geoip-lite';
import { Context, Next } from 'koa';
import util from 'util';

const execPromise = util.promisify(exec);

// MongoDB connection URI
const mongoURI = 'mongodb+srv://dankmater404:admin123@cluster0.9pq3hla.mongodb.net/Cluster0?retryWrites=true&w=majority&appName=Cluster0';

// Connect to MongoDB
mongoose.connect(mongoURI)
  .then(() => console.log('MongoDB connected successfully'))
  .catch((error: any) => console.error('Error connecting to MongoDB:', error));

// Define schema for system health logs
const systemHealthSchema = new mongoose.Schema({
  timestamp: { type: Date, default: Date.now },
  systemUptime: Number,
  systemDowntime: Number,
  networkTrafficIn: Number,
  networkTrafficOut: Number,
  healthCheckStatus: String,
  healthCheckDetails: String,
});

// Create model from the schema
const SystemHealth = mongoose.model('SystemHealth', systemHealthSchema);

// Function to get system uptime
const getSystemUptime = () => {
  const uptimeSeconds = os.uptime();
  return uptimeSeconds;
};

// Function to get system downtime (assuming system is up since the last reboot)
const getSystemDowntime = () => {
  const uptimeSeconds = os.uptime();
  const totalSecondsSinceBoot = process.uptime();
  const downtime = totalSecondsSinceBoot - uptimeSeconds;
  return downtime > 0 ? downtime : 0;
};

// Function to get network traffic (in and out)
const getNetworkTraffic = async () => {
  try {
    const { stdout } = await execPromise('cat /proc/net/dev');
    const lines = stdout.split('\n').slice(2); // Skip the first two lines

    let trafficIn = 0;
    let trafficOut = 0;

    for (const line of lines) {
      const columns = line.trim().split(/\s+/);
      if (columns.length >= 10) {
        trafficIn += parseInt(columns[1], 10);  // Bytes received
        trafficOut += parseInt(columns[9], 10); // Bytes transmitted
      }
    }

    return { trafficIn, trafficOut };
  } catch (error: any) {
    console.error('Error getting network traffic:', error);
    return { trafficIn: 0, trafficOut: 0 };
  }
};

// Function to perform health check
const performHealthCheck = async () => {
  try {
    const { stdout } = await execPromise('ping -c 1 8.8.8.8');
    return { status: 'Healthy', details: stdout };
  } catch (error: any) {
    return { status: 'Unhealthy', details: error.message };
  }
};

// Function to log system health data
export const logSystemHealth = async () => {
  const uptime = getSystemUptime();
  const downtime = getSystemDowntime();
  const networkTraffic = await getNetworkTraffic();
  const healthCheck = await performHealthCheck();

  const systemHealthEntry = new SystemHealth({
    systemUptime: uptime,
    systemDowntime: downtime,
    networkTrafficIn: networkTraffic.trafficIn,
    networkTrafficOut: networkTraffic.trafficOut,
    healthCheckStatus: healthCheck.status,
    healthCheckDetails: healthCheck.details,
  });

  try {
    await systemHealthEntry.save();
    console.log('System health data logged to MongoDB');
  } catch (error: any) {
    console.error('Error logging system health data to MongoDB:', error);
  }
};

// Function to start periodic logging
export const startLoggingSystemHealth = () => {
  setInterval(logSystemHealth, 5 * 60 * 1000);  // Log every 5 minutes
};
