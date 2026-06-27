const WebSocket = require('ws');
const Redis = require('ioredis');

let wss;
let redisSubscriber;
let redisPublisher;

function initializeWebSocket(server) {
  wss = new WebSocket.Server({ server });

  // Initialize Redis connection for pub/sub
  redisPublisher = new Redis({
    host: process.env.REDIS_HOST || 'localhost',
    port: process.env.REDIS_PORT || 6379,
    password: process.env.REDIS_PASSWORD || null
  });

  redisSubscriber = new Redis({
    host: process.env.REDIS_HOST || 'localhost',
    port: process.env.REDIS_PORT || 6379,
    password: process.env.REDIS_PASSWORD || null
  });

  wss.on('connection', (ws, req) => {
    console.log('New WebSocket client connected');

    // Subscribe to job progress channel
    redisSubscriber.subscribe('job_progress', (err, count) => {
      if (err) {
        console.error('Failed to subscribe to Redis channel:', err);
      } else {
        console.log(`Subscribed to ${count} Redis channel(s)`);
      }
    });

    // Handle messages from Redis
    redisSubscriber.on('message', (channel, message) => {
      if (channel === 'job_progress') {
        // Broadcast to all connected clients
        wss.clients.forEach(client => {
          if (client.readyState === WebSocket.OPEN) {
            client.send(message);
          }
        });
      }
    });

    ws.on('close', () => {
      console.log('WebSocket client disconnected');
      // Unsubscribe from all channels when client disconnects
      redisSubscriber.unsubscribe();
    });

    ws.on('error', (error) => {
      console.error('WebSocket error:', error);
    });
  });

  // Handle server shutdown
  process.on('SIGINT', () => {
    console.log('Shutting down WebSocket server...');
    wss.close();
    redisSubscriber.quit();
    redisPublisher.quit();
  });

  return wss;
}

function publishJobProgress(jobId, progressData) {
  const message = JSON.stringify({
    jobId,
    ...progressData
  });
  redisPublisher.publish('job_progress', message);
}

module.exports = {
  initializeWebSocket,
  publishJobProgress
};