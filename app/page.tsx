'use client';

import * as React from "react";
import { cn } from "../src/lib/utils";
import { Textarea } from "../components/ui/textarea";
import { Send, RefreshCw, Trash2, User, Bot } from 'lucide-react';
import { io, Socket } from 'socket.io-client';

type Clone = {
  name: string;
  emoji: string;
  personality: string;
  score: number;
  remix?: string;
};

type Message = {
  type: 'user' | 'ai' | 'system' | 'error';
  content: string;
  timestamp: Date;
};

const clones: Clone[] = [
  {
    name: "Elon",
    emoji: "🚀",
    personality: "Wants to colonize Mars. Rates ideas by how big and insane they are.",
    score: 93,
    remix: "Make this 100x bigger and use AI to automate everything.",
  },
  {
    name: "Naval",
    emoji: "🧘",
    personality: "Wants leverage and passive income. Rates ideas based on productizing oneself.",
    score: 75,
    remix: "Turn this into a productized service with media distribution built-in.",
  },
  {
    name: "Ali Abdaal",
    emoji: "📚",
    personality: "Thinks everything is a video idea or a Notion template.",
    score: 87,
    remix: "Could be a great YouTube series + productivity dashboard combo.",
  },
];

export default function Page() {
  const [messages, setMessages] = React.useState<Message[]>([]);
  const [inputMessage, setInputMessage] = React.useState('');
  const [selectedClone, setSelectedClone] = React.useState<Clone | null>(null);
  const [customName, setCustomName] = React.useState('');
  const [isConnected, setIsConnected] = React.useState(false);
  const [isTyping, setIsTyping] = React.useState(false);
  const [isInitializing, setIsInitializing] = React.useState(false);
  const messagesEndRef = React.useRef<HTMLDivElement>(null);
  const socketRef = React.useRef<Socket | null>(null);

  React.useEffect(() => {
    const socket = io('http://localhost:3001');
    socketRef.current = socket;

    socket.on('connect', () => {
      setIsConnected(true);
      setMessages([{
        type: 'system',
        content: 'Connected to Clone Council! Select a clone or enter a name to start chatting.',
        timestamp: new Date()
      }]);
    });

    socket.on('disconnect', () => {
      setIsConnected(false);
      setMessages(prev => [...prev, {
        type: 'error',
        content: 'Connection lost. Please refresh the page.',
        timestamp: new Date()
      }]);
    });

    socket.on('voiceboard-ready', (data: any) => {
      console.log('Voiceboard ready:', data);
      setIsInitializing(false);
      setMessages(prev => [...prev, {
        type: 'system',
        content: `Voiceboard initialized for ${data.personName}. Start chatting!`,
        timestamp: new Date()
      }]);
    });

    socket.on('response', (data: any) => {
      console.log('Received response:', data);
      setMessages(prev => [...prev, {
        type: 'ai',
        content: data.message,
        timestamp: new Date(data.timestamp) || new Date()
      }]);
      setIsTyping(false);
    });

    socket.on('typing', (typing: boolean) => {
      console.log('Typing indicator:', typing);
      setIsTyping(typing);
    });

    socket.on('status', (data: any) => {
      console.log('Status message:', data);
      setMessages(prev => [...prev, {
        type: 'system',
        content: data.message,
        timestamp: new Date()
      }]);
    });

    socket.on('error', (data: any) => {
      console.log('Error received:', data);
      setMessages(prev => [...prev, {
        type: 'error',
        content: data.message,
        timestamp: new Date()
      }]);
      setIsTyping(false);
      setIsInitializing(false);
    });

    return () => {
      socket.disconnect();
    };
  }, []);

  React.useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  const handleCreateVoiceboard = () => {
    const personName = customName.trim() || selectedClone?.name;
    if (!personName) return;
    console.log('Creating voiceboard for:', personName);
    setIsInitializing(true);
    socketRef.current?.emit('create-voiceboard', { personName });
  };

  const handleSendMessage = () => {
    if (!inputMessage.trim() || isTyping || isInitializing) return;
    console.log('Sending message:', inputMessage);
    setMessages(prev => [...prev, {
      type: 'user',
      content: inputMessage,
      timestamp: new Date()
    }]);
    socketRef.current?.emit('chat', { message: inputMessage });
    setInputMessage('');
  };

  const handleClearConversation = () => {
    socketRef.current?.emit('clear-conversation', {});
    setMessages([{
      type: 'system',
      content: 'Conversation cleared',
      timestamp: new Date()
    }]);
  };

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSendMessage();
    }
  };

  // Check if we should show the chat interface
  const shouldShowChat = selectedClone || customName.trim();

  return (
    <div className="min-h-screen bg-gradient-to-br from-purple-600 via-pink-500 to-orange-400 text-white flex flex-col">
      {/* Header */}
      <div className="p-6 text-center">
        <h1 className="text-5xl font-extrabold mb-2">🧠 Clone Council</h1>
        <p className="text-lg opacity-90">
          Chat with AI clones of famous personalities
        </p>
      </div>

      {/* Clone Selection */}
      {!shouldShowChat ? (
        <div className="flex-1 flex flex-col items-center justify-center px-4">
          <div className="bg-white bg-opacity-10 backdrop-blur-sm rounded-2xl p-8 max-w-2xl w-full border border-white border-opacity-20">
            <h2 className="text-2xl font-semibold mb-6 text-center">Pick Your Clone or Enter a Name:</h2>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-6">
              {clones.map((clone) => (
                <button
                  key={clone.name}
                  onClick={() => setSelectedClone(clone)}
                  className="p-4 rounded-xl border border-white border-opacity-20 hover:bg-white hover:bg-opacity-10 transition-all duration-200 text-left"
                >
                  <div className="text-2xl mb-2">{clone.emoji}</div>
                  <div className="font-semibold">{clone.name}</div>
                  <div className="text-sm opacity-80 mt-1">{clone.personality}</div>
                </button>
              ))}
            </div>
            <input
              type="text"
              placeholder="Or type a custom name..."
              className="w-full px-4 py-2 rounded-lg mt-4 text-black"
              value={customName}
              onChange={e => setCustomName(e.target.value)}
              disabled={isInitializing}
            />
            <button
              onClick={handleCreateVoiceboard}
              disabled={!isConnected || (!selectedClone && !customName.trim())}
              className="w-full bg-black bg-opacity-70 hover:bg-opacity-90 px-6 py-3 rounded-full text-white font-bold disabled:opacity-50 mt-4"
            >
              {!isConnected ? 'Connecting...' : 'Start Chatting'}
            </button>
          </div>
        </div>
      ) : (
        <>
          {/* Chat Header */}
          <div className="bg-white bg-opacity-10 backdrop-blur-sm border-b border-white border-opacity-20 p-4">
            <div className="max-w-4xl mx-auto flex items-center justify-between">
              <div className="flex items-center space-x-3">
                <div className="text-2xl">{selectedClone?.emoji || '🧑'}</div>
                <div>
                  <h2 className="text-xl font-semibold">{customName.trim() || selectedClone?.name}</h2>
                  <p className="text-sm opacity-80">
                    {isInitializing ? 'Initializing...' : 'AI Personality Active'}
                  </p>
                </div>
              </div>
              <div className="flex items-center space-x-2">
                <button
                  onClick={() => { setSelectedClone(null); setCustomName(''); }}
                  className="p-2 rounded-lg hover:bg-white hover:bg-opacity-10 transition"
                  title="Change clone or name"
                >
                  <RefreshCw className="w-5 h-5" />
                </button>
                <button
                  onClick={handleClearConversation}
                  className="p-2 rounded-lg hover:bg-white hover:bg-opacity-10 transition"
                  title="Clear conversation"
                >
                  <Trash2 className="w-5 h-5" />
                </button>
              </div>
            </div>
          </div>

          {/* Messages Area */}
          <div className="flex-1 overflow-y-auto p-4">
            <div className="max-w-4xl mx-auto space-y-4">
              {messages.map((message, index) => (
                <div
                  key={index}
                  className={cn(
                    "flex",
                    message.type === 'user' ? 'justify-end' : 'justify-start'
                  )}
                >
                  <div
                    className={cn(
                      "max-w-lg px-4 py-3 rounded-2xl backdrop-blur-sm",
                      message.type === 'user'
                        ? 'bg-white bg-opacity-20 text-white'
                        : message.type === 'ai'
                        ? 'bg-black bg-opacity-40 text-white'
                        : message.type === 'error'
                        ? 'bg-red-500 bg-opacity-80 text-white'
                        : 'bg-white bg-opacity-10 text-white italic'
                    )}
                  >
                    <div className="flex items-start space-x-2">
                      {message.type === 'ai' && (
                        <Bot className="w-5 h-5 mt-0.5 flex-shrink-0" />
                      )}
                      <p className="text-sm">{message.content}</p>
                    </div>
                  </div>
                </div>
              ))}
              {isTyping && (
                <div className="flex justify-start">
                  <div className="bg-black bg-opacity-40 text-white px-4 py-3 rounded-2xl">
                    <div className="flex space-x-2">
                      <div className="w-2 h-2 bg-white rounded-full animate-bounce"></div>
                      <div className="w-2 h-2 bg-white rounded-full animate-bounce" style={{ animationDelay: '0.1s' }}></div>
                      <div className="w-2 h-2 bg-white rounded-full animate-bounce" style={{ animationDelay: '0.2s' }}></div>
                    </div>
                  </div>
                </div>
              )}
              <div ref={messagesEndRef} />
            </div>
          </div>

          {/* Input Area */}
          <div className="bg-white bg-opacity-10 backdrop-blur-sm border-t border-white border-opacity-20 p-4">
            <div className="max-w-4xl mx-auto">
              <div className="flex space-x-3">
                <Textarea
                  placeholder={isInitializing ? "Initializing voiceboard..." : "Type your message..."}
                  className="flex-1 bg-white text-black placeholder:text-gray-500 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:ring-opacity-50 resize-none min-h-[40px]"
                  textColor="black"
                  value={inputMessage}
                  onChange={(e) => setInputMessage(e.target.value)}
                  onKeyPress={handleKeyPress}
                  disabled={isInitializing || isTyping}
                  rows={1}
                />
                <button
                  onClick={handleSendMessage}
                  disabled={!inputMessage.trim() || isTyping || isInitializing}
                  className="bg-black bg-opacity-70 hover:bg-opacity-90 text-white p-3 rounded-xl transition duration-200 disabled:opacity-50"
                >
                  <Send className="w-5 h-5" />
                </button>
              </div>
            </div>
          </div>
        </>
      )}
    </div>
  );
}
