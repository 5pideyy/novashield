import mongoose from 'mongoose';

const mongoURI = 'mongodb+srv://admin:admin@cluster0.1wgqgg8.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0';

let isConnected = false;

export const connectToDatabase = async (): Promise<void> => {
  if (!isConnected) {
    try {
      // No need to specify `useNewUrlParser` or `useUnifiedTopology` in Mongoose 6.x
      await mongoose.connect(mongoURI);
      isConnected = true;
      console.log('MongoDB connected successfully');
    } catch (error) {
      console.error('Error connecting to MongoDB:', error);
      throw error;
    }
  } else {
    console.log('Already connected to MongoDB');
  }
};
