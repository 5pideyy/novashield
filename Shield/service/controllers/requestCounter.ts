import mongoose from 'mongoose';
import { Context, Next } from 'koa';
import { connectToDatabase } from './db';  // Import the connection from db.ts

// Define schema to store request count
const requestCountSchema = new mongoose.Schema({
  count: { type: Number, default: 0 },
});

// Create model from the schema (only after database connection is established)
let RequestCount: mongoose.Model<any> | undefined = undefined;

// Function to initialize and return the RequestCount model
const initializeModel = (): mongoose.Model<any> => {
  if (!RequestCount) {
    RequestCount = mongoose.model('RequestCount', requestCountSchema);
  }
  return RequestCount;
};

// Middleware function to count requests
export const countRequests = async (ctx: Context, next: Next) => {
  try {
    // Ensure MongoDB is connected
    await connectToDatabase();
    
    // Initialize and get the RequestCount model after connecting to the DB
    const RequestCountModel = initializeModel();

    // Fetch current count from MongoDB
    let countDocument = await RequestCountModel.findOne();
    
    // If there is no document, create one
    if (!countDocument) {
      countDocument = new RequestCountModel({ count: 0 });
    }

    // Increment the request count
    countDocument.count += 1;
    
    // Save the updated count to MongoDB
    await countDocument.save();
    console.log(`Total requests so far: ${countDocument.count}`);
    
  } catch (error) {
    console.error('Error in countRequests middleware:', error);
  }

  // Pass control to the next middleware
  await next();
};

// Function to get the total number of requests
export const getTotalRequests = async () => {
  try {
    // Ensure MongoDB is connected
    await connectToDatabase();
    
    // Initialize and get the RequestCount model after connecting to the DB
    const RequestCountModel = initializeModel();

    const countDocument = await RequestCountModel.findOne();
    return countDocument ? countDocument.count : 0;
  } catch (error) {
    console.error('Error fetching total request count:', error);
    return 0;
  }
};
