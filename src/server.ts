// server.ts
import express, { Request, Response, NextFunction } from 'express';
import { createServer } from 'http';
import { Server, Socket } from 'socket.io';
import cors from 'cors';
import dotenv from 'dotenv';
import { Voiceboard } from './voiceboard';

dotenv.config();

// Define request/response types
interface CreateVoiceboardRequest {
  personName: string;
  sessionId: string;
}

interface ChatRequest {
  sessionId: string;
  message: string;
}

interface VoiceboardResponse {
  success?: boolean;
  message?: string;
  sessionId?: string;
  response?: string;
  error?: string;
}

// Socket event types
interface ServerToClientEvents {
  'status': (data: { message: string }) => void;
  'voiceboard-ready': (data: { personName: string }) => void;
  'response': (data: { message: string; timestamp: Date }) => void;
  'typing': (isTyping: boolean) => void;
  'error': (data: { message: string }) => void;
  'conversation-cleared': () => void;
}

interface ClientToServerEvents {
  'create-voiceboard': (data: { personName: string }) => void;
  'chat': (data: { message: string }) => void;
  'clear-conversation': () => void;
}

interface InterServerEvents {
  ping: () => void;
}

interface SocketData {
  personName: string;
}

const app = express();
const httpServer = createServer(app);

// Typed Socket.IO server
const io = new Server<ClientToServerEvents, ServerToClientEvents, InterServerEvents, SocketData>(httpServer, {
    cors: {
      origin: process.env.CLIENT_URL || "http://localhost:3000",
      methods: ["GET", "POST"]
    }
});

app.use(cors());
app.use(express.json());

// Store voiceboard instances per session
const voiceboards = new Map<string, Voiceboard>();

// Typed REST API endpoints
app.post('/api/voiceboard/create', async (
  req: Request,
  res: Response,
  next: NextFunction
) => {
  try {
    const { personName, sessionId } = req.body as CreateVoiceboardRequest;
    
    if (!personName || !sessionId) {
      res.status(400).json({ 
        error: 'personName and sessionId are required' 
      });
      return;
    }
    
    const voiceboard = new Voiceboard(personName);
    await voiceboard.initialize();
    
    voiceboards.set(sessionId, voiceboard);
    
    res.json({ 
      success: true, 
      message: `Voiceboard created for ${personName}`,
      sessionId 
    });
  } catch (error) {
    console.error('Error creating voiceboard:', error);
    res.status(500).json({ 
      error: error instanceof Error ? error.message : 'Unknown error occurred' 
    });
  }
});

app.post('/api/voiceboard/chat', async (
  req: Request,
  res: Response,
  next: NextFunction
) => {
  try {
    const { sessionId, message } = req.body as ChatRequest;
    
    if (!sessionId || !message) {
      res.status(400).json({ 
        error: 'sessionId and message are required' 
      });
      return;
    }
    
    const voiceboard = voiceboards.get(sessionId);
    if (!voiceboard) {
      res.status(404).json({ 
        error: 'Voiceboard not found. Please create a voiceboard first.' 
      });
      return;
    }
    
    const response = await voiceboard.chat(message);
    res.json({ response });
  } catch (error) {
    console.error('Error in chat:', error);
    res.status(500).json({ 
      error: error instanceof Error ? error.message : 'Unknown error occurred' 
    });
  }
});

// Additional endpoints with proper typing
app.get('/api/voiceboard/status/:sessionId', async (
  req: Request,
  res: Response,
  next: NextFunction
) => {
  const { sessionId } = req.params;
  const voiceboard = voiceboards.get(sessionId);
  
  if (voiceboard) {
    res.json({ 
      exists: true, 
      personName: voiceboard.getPersonName() // You'd need to add this method
    });
  } else {
    res.json({ exists: false });
  }
});

app.delete('/api/voiceboard/:sessionId', async (
  req: Request,
  res: Response,
  next: NextFunction
) => {
  const { sessionId } = req.params;
  const deleted = voiceboards.delete(sessionId);
  
  if (deleted) {
    res.json({ 
      success: true, 
      message: 'Voiceboard deleted successfully' 
    });
  } else {
    res.status(404).json({ 
      error: 'Voiceboard not found' 
    });
  }
});

// Error handling middleware
app.use((err: Error, req: Request, res: Response, next: NextFunction) => {
  console.error('Global error handler:', err);
  res.status(500).json({ 
    error: 'Internal server error',
    message: process.env.NODE_ENV === 'development' ? err.message : undefined
  });
});

// Typed Socket.io handlers
io.on('connection', (socket: Socket<ClientToServerEvents, ServerToClientEvents>) => {
  console.log('User connected:', socket.id);
  
  socket.on('create-voiceboard', async (data) => {
    try {
      const { personName } = data;
      
      if (!personName) {
        socket.emit('error', { message: 'Person name is required' });
        return;
      }
      
      const voiceboard = new Voiceboard(personName);
      
      socket.emit('status', { message: 'Initializing voiceboard...' });
      await voiceboard.initialize();
      
      voiceboards.set(socket.id, voiceboard);
      socket.data.personName = personName;
      
      socket.emit('voiceboard-ready', { personName });
    } catch (error) {
      console.error('Socket error creating voiceboard:', error);
      socket.emit('error', { 
        message: error instanceof Error ? error.message : 'Failed to create voiceboard' 
      });
    }
  });
  
  socket.on('chat', async (data) => {
    try {
      const { message } = data;
      
      if (!message) {
        socket.emit('error', { message: 'Message cannot be empty' });
        return;
      }
      
      const voiceboard = voiceboards.get(socket.id);
      
      if (!voiceboard) {
        socket.emit('error', { message: 'Please create a voiceboard first' });
        return;
      }
      
      // Send typing indicator
      socket.emit('typing', true);
      
      const response = await voiceboard.chat(message);
      
      socket.emit('response', { 
        message: response,
        timestamp: new Date()
      });
      socket.emit('typing', false);
    } catch (error) {
      console.error('Socket error in chat:', error);
      socket.emit('error', { 
        message: error instanceof Error ? error.message : 'Failed to process message' 
      });
      socket.emit('typing', false);
    }
  });
  
  socket.on('clear-conversation', () => {
    try {
      const voiceboard = voiceboards.get(socket.id);
      if (voiceboard) {
        voiceboard.clearConversation();
        socket.emit('conversation-cleared');
      } else {
        socket.emit('error', { message: 'No active voiceboard found' });
      }
    } catch (error) {
      console.error('Socket error clearing conversation:', error);
      socket.emit('error', { 
        message: 'Failed to clear conversation' 
      });
    }
  });
  
  socket.on('disconnect', () => {
    voiceboards.delete(socket.id);
    console.log('User disconnected:', socket.id);
  });
});

// Health check endpoint
app.get('/health', (req: Request, res: Response<{ status: string; timestamp: string }>) => {
  res.json({ 
    status: 'ok', 
    timestamp: new Date().toISOString() 
  });
});

const PORT = parseInt(process.env.PORT || '3001', 10);

httpServer.listen(PORT, () => {
  console.log(`🚀 Server running on port ${PORT}`);
  console.log(`🔗 Health check: http://localhost:${PORT}/health`);
});

// Graceful shutdown
process.on('SIGTERM', () => {
  console.log('SIGTERM signal received: closing HTTP server');
  httpServer.close(() => {
    console.log('HTTP server closed');
  });
});