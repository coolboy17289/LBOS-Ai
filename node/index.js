require('dotenv').config();
const express = require('express');
const http = require('http');
const WebSocket = require('ws');
const path = require('path');
const { QueueManager } = require('./jobs/queueManager');
const { sequelize } = require('./models');
const authRoutes = require('./routes/auth');
const jobRoutes = require('./routes/jobs');
const modelRoutes = require('./routes/models');
const evalRoutes = require('./routes/evaluations');
const logRoutes = require('./routes/logs');
const { initializeWebSocket } = require('./ws/websocket');

const app = express();
const server = http.createServer(app);
const port = process.env.PORT || 5000; // Changed default to 5000 to avoid conflict with React dev server

// Middleware
app.use(express.json());
app.use(express.urlencoded({ extended: true }));
app.use(require('cors')());
app.use(require('helmet')());

// Routes
app.use('/api/auth', authRoutes);
app.use('/api/jobs', jobRoutes);
app.use('/api/models', modelRoutes);
app.use('/api/evaluations', evalRoutes);
app.use('/api/logs', logRoutes);

// Serve static files from React build app
app.use(express.static(path.join(__dirname, '..', 'frontend', 'build')));
// Handles any requests that don't match the ones above
app.get('*', (req, res) => {
  res.sendFile(path.join(__dirname, '..', 'frontend', 'build', 'index.html'));
});

// Health check
app.get('/health', (req, res) => {
  res.status(200).json({ status: 'OK', timestamp: new Date().toISOString() });
});

// Initialize WebSocket
const wss = initializeWebSocket(server);

// Database connection
sequelize.authenticate()
  .then(() => {
    console.log('Database connected successfully');
    return sequelize.sync(); // Create tables if they don't exist
  })
  .then(() => {
    // Initialize job queues
    QueueManager.initializeQueues();

    server.listen(port, () => {
      console.log(`Server running on port ${port}`);
    });
  })
  .catch(err => {
    console.error('Unable to start server:', err);
    process.exit(1);
  });

module.exports = { app, server };