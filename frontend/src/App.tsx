import React, { useState } from 'react';
import './App.css';

interface Message {
  id: string;
  text: string;
  isUser: boolean;
  timestamp: string;
}

interface ChatResponse {
  response: string;
  conversationInfo: {
    messageCount: number;
    estimatedTokens: number;
    personName: string;
    personalityContext: string;
  };
  timestamp: string;
}

function App() {
  const [messages, setMessages] = useState<Message[]>([]);
  const [inputMessage, setInputMessage] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [userId] = useState(`user_${Date.now()}`);

  const sendMessage = async () => {
    if (!inputMessage.trim()) return;

    const userMessage: Message = {
      id: Date.now().toString(),
      text: inputMessage,
      isUser: true,
      timestamp: new Date().toISOString()
    };

    setMessages(prev => [...prev, userMessage]);
    setInputMessage('');
    setIsLoading(true);

    try {
      const response = await fetch('/api/chat', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          message: inputMessage,
          userId,
          personName: 'ReactAssistant',
          personalityContext: 'You are a helpful and friendly AI assistant for the React frontend.'
        }),
      });

      const data: ChatResponse = await response.json();

      const aiMessage: Message = {
        id: (Date.now() + 1).toString(),
        text: data.response,
        isUser: false,
        timestamp: data.timestamp
      };

      setMessages(prev => [...prev, aiMessage]);
    } catch (error) {
      console.error('Error sending message:', error);
    } finally {
      setIsLoading(false);
    }
  };

  const clearConversation = async () => {
    try {
      await fetch(`/api/conversation/${userId}`, {
        method: 'DELETE',
      });
      setMessages([]);
    } catch (error) {
      console.error('Error clearing conversation:', error);
    }
  };

  return (
    <div className="app">
      <div className="chat-container">
        <div className="chat-header">
          <h1>AI Chat Assistant</h1>
          <button onClick={clearConversation} className="clear-button">
            Clear Chat
          </button>
        </div>
        
        <div className="messages-container">
          {messages.map((message) => (
            <div key={message.id} className={`message ${message.isUser ? 'user' : 'ai'}`}>
              <div className="message-content">{message.text}</div>
              <div className="message-timestamp">
                {new Date(message.timestamp).toLocaleTimeString()}
              </div>
            </div>
          ))}
          {isLoading && (
            <div className="message ai">
              <div className="message-content">Thinking...</div>
            </div>
          )}
        </div>

        <div className="input-container">
          <input
            type="text"
            value={inputMessage}
            onChange={(e) => setInputMessage(e.target.value)}
            onKeyPress={(e) => e.key === 'Enter' && sendMessage()}
            placeholder="Type your message..."
            disabled={isLoading}
            className="message-input"
          />
          <button 
            onClick={sendMessage} 
            disabled={isLoading || !inputMessage.trim()}
            className="send-button"
          >
            Send
          </button>
        </div>
      </div>
    </div>
  );
}

export default App; 