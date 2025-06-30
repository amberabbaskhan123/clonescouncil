# Conversational Chat System with LangGraph

A Node.js/TypeScript conversational chat system using LangGraph with smart memory management for token optimization, powered by GPT-4.

## Features

- 🤖 **GPT-4 Integration**: Powered by OpenAI's GPT-4 model
- 🧠 **Smart Memory Management**: Uses LangGraph's MemorySaver for efficient conversation state persistence
- 💬 **Conversation State**: Maintains conversation history and context
- 🎭 **Personality Context**: Customizable AI personality and behavior
- 📊 **Token Optimization**: Tracks estimated tokens for cost management
- 🔄 **Thread Persistence**: Conversations persist across sessions using thread IDs
- 🧪 **Comprehensive Testing**: Full test suite with Jest

## Quick Start

### 1. Install Dependencies

```bash
npm install
```

### 2. Set Environment Variables

Create a `.env` file in the root directory:

```env
OPENAI_API_KEY=your_openai_api_key_here
```

### 3. Start the Demo Server

```bash
npm start
```

The server will run on `http://localhost:3001`

### 4. Test the API

Open `examples/demo.html` in your browser to see a live demo of the chat system.

## API Endpoints

### POST /api/chat
Send a message to the AI assistant.

**Request Body:**
```json
{
  "message": "Hello!",
  "userId": "user123",
  "personName": "AI Assistant",
  "personalityContext": "You are a helpful and friendly AI assistant."
}
```

**Response:**
```json
{
  "response": "Hello! I'm AI Assistant. You are a helpful and friendly AI assistant. I received your message: \"Hello!\". How can I help you today?",
  "conversationInfo": {
    "messageCount": 1,
    "estimatedTokens": 45,
    "personName": "AI Assistant",
    "personalityContext": "You are a helpful and friendly AI assistant."
  },
  "timestamp": "2024-01-15T10:30:00.000Z"
}
```

### GET /api/conversation/:userId
Get conversation information for a user.

**Response:**
```json
{
  "messageCount": 5,
  "estimatedTokens": 234,
  "personName": "AI Assistant",
  "personalityContext": "You are a helpful and friendly AI assistant."
}
```

### DELETE /api/conversation/:userId
Clear conversation history for a user.

**Response:**
```json
{
  "message": "Conversation cleared successfully"
}
```

## Frontend Integration

### React Example

```tsx
import React, { useState } from 'react';

const ChatComponent = () => {
  const [messages, setMessages] = useState([]);
  const [inputMessage, setInputMessage] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const userId = `user_${Date.now()}`;

  const sendMessage = async () => {
    if (!inputMessage.trim()) return;

    setIsLoading(true);
    try {
      const response = await fetch('http://localhost:3001/api/chat', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          message: inputMessage,
          userId,
          personName: 'TestAssistant',
          personalityContext: 'You are a helpful AI assistant.'
        }),
      });

      const data = await response.json();
      setMessages(prev => [...prev, 
        { text: inputMessage, isUser: true },
        { text: data.response, isUser: false }
      ]);
      setInputMessage('');
    } catch (error) {
      console.error('Error:', error);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div>
      <div className="messages">
        {messages.map((msg, i) => (
          <div key={i} className={msg.isUser ? 'user' : 'ai'}>
            {msg.text}
          </div>
        ))}
      </div>
      <input
        value={inputMessage}
        onChange={(e) => setInputMessage(e.target.value)}
        onKeyPress={(e) => e.key === 'Enter' && sendMessage()}
        placeholder="Type your message..."
        disabled={isLoading}
      />
      <button onClick={sendMessage} disabled={isLoading}>
        Send
      </button>
    </div>
  );
};
```

### Vue.js Example

```vue
<template>
  <div>
    <div class="messages">
      <div v-for="message in messages" :key="message.id" :class="message.isUser ? 'user' : 'ai'">
        {{ message.text }}
      </div>
    </div>
    <input v-model="inputMessage" @keyup.enter="sendMessage" placeholder="Type your message..." />
    <button @click="sendMessage" :disabled="isLoading">Send</button>
  </div>
</template>

<script setup>
import { ref } from 'vue';

const messages = ref([]);
const inputMessage = ref('');
const isLoading = ref(false);
const userId = `user_${Date.now()}`;

const sendMessage = async () => {
  if (!inputMessage.value.trim()) return;
  
  isLoading.value = true;
  try {
    const response = await fetch('http://localhost:3001/api/chat', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        message: inputMessage.value,
        userId,
        personName: 'TestAssistant'
      }),
    });
    
    const data = await response.json();
    messages.value.push(
      { id: Date.now(), text: inputMessage.value, isUser: true },
      { id: Date.now() + 1, text: data.response, isUser: false }
    );
    inputMessage.value = '';
  } catch (error) {
    console.error('Error:', error);
  } finally {
    isLoading.value = false;
  }
};
</script>
```

### Vanilla JavaScript Example

```javascript
class ChatClient {
  constructor(userId, options = {}) {
    this.userId = userId;
    this.baseUrl = options.baseUrl || 'http://localhost:3001';
  }

  async sendMessage(message) {
    const response = await fetch(`${this.baseUrl}/api/chat`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        message,
        userId: this.userId,
        personName: 'AI Assistant'
      }),
    });
    
    return await response.json();
  }

  async clearConversation() {
    const response = await fetch(`${this.baseUrl}/api/conversation/${this.userId}`, {
      method: 'DELETE',
    });
    
    return await response.json();
  }
}

// Usage
const chatClient = new ChatClient('user123');
chatClient.sendMessage('Hello!')
  .then(data => console.log('Response:', data.response))
  .catch(error => console.error('Error:', error));
```

## Architecture

### Core Components

- **ChatService**: Main service class for handling chat operations
- **ChatWorkflow**: LangGraph workflow for processing messages
- **MemorySaver**: Handles conversation state persistence
- **MemoryConfig**: Configuration for system prompts and token limits

### State Management

The system uses LangGraph's `MessagesState` and `MemorySaver` for:
- **Message History**: Maintains conversation context
- **Thread Persistence**: Saves conversations using unique thread IDs
- **Token Tracking**: Estimates token usage for cost optimization
- **Personality Context**: Maintains AI assistant personality across conversations

### Key Features

1. **Smart Memory**: Uses LangGraph's built-in memory management
2. **Thread Persistence**: Conversations persist across server restarts
3. **Token Optimization**: Tracks estimated tokens to manage costs
4. **Flexible Personality**: Customizable AI assistant behavior
5. **Error Handling**: Comprehensive error handling and validation

## Testing

Run the test suite:

```bash
# Run all tests
npm test

# Run tests in watch mode
npm run test:watch

# Run tests with coverage
npm run test:coverage

# Run manual tests
npm run test:manual
```

## Development

### Project Structure

```
src/
├── services/
│   └── ChatService.ts          # Main chat service
├── workflows/
│   └── chatWorkflow.ts         # LangGraph workflow
├── memory/
│   └── memoryConfig.ts         # Memory configuration
├── types/
│   └── chat.ts                 # TypeScript type definitions
└── server.js                   # Demo server

tests/
├── ChatService.test.ts         # Service tests
├── chatWorkflow.test.ts        # Workflow tests
└── run-tests.ts               # Manual test runner

examples/
├── demo.html                   # Live demo
└── frontend-integration.md     # Integration examples
```

### Building

```bash
# Build TypeScript
npm run build

# Start development server
npm run dev
```

## Configuration

### Environment Variables

- `OPENAI_API_KEY`: Your OpenAI API key
- `PORT`: Server port (default: 3001)

### ChatService Configuration

```typescript
const config: ChatServiceConfig = {
  personName: 'AI Assistant',
  personalityContext: 'You are a helpful and friendly AI assistant.',
  openaiApiKey: process.env.OPENAI_API_KEY!,
  modelName: 'gpt-4',
};
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests for new functionality
5. Run the test suite
6. Submit a pull request

## License

MIT License - see LICENSE file for details.
