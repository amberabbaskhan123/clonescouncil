# Chat Frontend

A React frontend for the conversational chat system.

## Quick Start

### 1. Install Dependencies

```bash
cd frontend
npm install
```

### 2. Start the Backend Server

In a separate terminal, start the backend server:

```bash
# From the root directory
npm start
```

The backend will run on `http://localhost:3001`

### 3. Start the Frontend

```bash
npm start
```

The frontend will run on `http://localhost:3000`

## Features

- Real-time chat interface
- Message history
- Loading states
- Error handling
- Clear conversation functionality
- Responsive design

## API Proxy

The frontend is configured to proxy API requests to the backend server running on port 3001. This means you can make requests to `/api/*` and they will be forwarded to the backend.

## Development

- Built with React 18 and TypeScript
- Uses Vite for fast development
- Includes modern CSS with animations
- Fully responsive design 