import mongoose from 'mongoose';
import { Context, Next } from 'koa';

// MongoDB connection URI
const mongoURI = 'mongodb+srv://dankmater404:admin123@cluster0.9pq3hla.mongodb.net/Cluster0?retryWrites=true&w=majority&appName=Cluster0';

// Connect to MongoDB
mongoose.connect(mongoURI)
  .then(() => console.log('MongoDB connected successfully'))
  .catch(error => console.error('Error connecting to MongoDB:', error));

// Define schema to store request count
const requestCountSchema = new mongoose.Schema({
  count: { type: Number, default: 0 },
});

// Create model from the schema
const RequestCount = mongoose.model('RequestCount', requestCountSchema);

// Middleware function to count requests
export const countRequests = async (ctx: Context, next: Next) => {
  // Fetch current count from MongoDB
  let countDocument = await RequestCount.findOne();
  
  // If there is no document, create one
  if (!countDocument) {
    countDocument = new RequestCount({ count: 0 });
  }

  // Increment the request count
  countDocument.count += 1;
  
  // Save the updated count to MongoDB
  try {
    await countDocument.save();
    console.log(`Total requests so far: ${countDocument.count}`);
  } catch (error) {
    console.error('Error updating request count:', error);
  }

  // Pass control to the next middleware
  await next();
};

// Function to get the total number of requests
export const getTotalRequests = async () => {
  const countDocument = await RequestCount.findOne();
  return countDocument ? countDocument.count : 0;
};
