/**
 * Streaming Response Service
 * Handles real-time token streaming from models to clients via WebSockets and SSE
 */
const WebSocket = require('ws');
const { v4: uuidv4 } = require('uuid');
const logger = require('../utils/logger');

class StreamingService {
  constructor(server) {
    this.wss = new WebSocket.Server({ noServer: true });
    this.activeStreams = new Map(); // streamId -> { clients, metadata }
    this.setupWebSocketServer();
  }

  /**
   * Setup WebSocket server for streaming
   */
  setupWebSocketServer() {
    this.wss.on('connection', (ws, req) => {
      const clientId = uuidv4();
      const streamId = new URLSearchParams(new URL(req.url, `ws://${req.headers.host}`).search).get('streamId');

      if (!streamId) {
        ws.close(4000, 'Missing streamId parameter');
        return;
      }

      // Initialize stream if not exists
      if (!this.activeStreams.has(streamId)) {
        this.activeStreams.set(streamId, {
          clients: new Set(),
          metadata: {
            createdAt: Date.now(),
            lastActivity: Date.now(),
            tokenCount: 0
          }
        });
      }

      const stream = this.activeStreams.get(streamId);
      stream.clients.add(ws);
      stream.metadata.lastActivity = Date.now();

      // Send initial connection confirmation
      ws.send(JSON.stringify({
        type: 'connection_established',
        streamId,
        clientId,
        timestamp: Date.now()
      }));

      ws.on('message', (message) => {
        try {
          const data = JSON.parse(message);
          this.handleClientMessage(ws, streamId, data);
        } catch (error) {
          ws.send(JSON.stringify({
            type: 'error',
            message: 'Invalid message format'
          }));
        }
      });

      ws.on('close', () => {
        if (stream) {
          stream.clients.delete(ws);
          stream.metadata.lastActivity = Date.now();

          // Clean up empty streams
          if (stream.clients.size === 0) {
            this.activeStreams.delete(streamId);
            logger.info(`Stream ${streamId} closed - no remaining clients`);
          }
        }
      });

      ws.on('error', (error) => {
        logger.error(`WebSocket error for client ${clientId}`, { error: error.message });
      });

      logger.info(`WebSocket client connected`, {
        clientId,
        streamId,
        totalClients: stream.clients.size
      });
    });

    // Handle HTTP upgrade for WebSocket
    server.on('upgrade', (request, socket, head) => {
      this.wss.handleUpgrade(request, socket, head, (ws) => {
        this.wss.emit('connection', ws, request);
      });
    });
  }

  /**
   * Handle messages from clients
   * @param {WebSocket} ws - Client WebSocket connection
   * @param {string} streamId - Stream identifier
   * @param {Object} message - Parsed message from client
   */
  handleClientMessage(ws, streamId, message) {
    const stream = this.activeStreams.get(streamId);
    if (!stream) {
      ws.send(JSON.stringify({
        type: 'error',
        message: 'Stream not found or expired'
      }));
      return;
    }

    switch (message.type) {
      case 'start_generation':
        this.handleStartGeneration(ws, streamId, message.payload);
        break;

      case 'cancel_generation':
        this.handleCancelGeneration(ws, streamId);
        break;

      case 'ping':
        ws.send(JSON.stringify({ type: 'pong', timestamp: Date.now() }));
        break;

      default:
        ws.send(JSON.stringify({
          type: 'error',
          message: 'Unknown message type'
        }));
    }
  }

  /**
   * Handle start generation request
   * @param {WebSocket} ws - Client WebSocket
   * @param {string} streamId - Stream identifier
   * @param {Object} payload - Generation parameters
   */
  async handleStartGeneration(ws, streamId, payload) {
    const stream = this.activeStreams.get(streamId);
    if (!stream) return;

    // Update metadata
    stream.metadata = {
      ...stream.metadata,
      startedAt: Date.now(),
      prompt: payload.prompt,
      params: { ...payload },
      tokenCount: 0
    };

    // Notify client generation started
    ws.send(JSON.stringify({
      type: 'generation_started',
      streamId,
      timestamp: Date.now()
    }));

    try {
      // Forward request to model router
      const modelResponse = await this.forwardToModel(streamId, payload);

      // Stream response back to client
      await this.streamResponseToClient(ws, streamId, modelResponse);

      // Mark stream as completed
      stream.metadata.completedAt = Date.now();
      stream.metadata.status = 'completed';

      ws.send(JSON.stringify({
        type: 'generation_complete',
        streamId,
        tokenCount: stream.metadata.tokenCount,
        timestamp: Date.now()
      }));
    } catch (error) {
      logger.error(`Error in generation stream ${streamId}`, { error: error.message });

      ws.send(JSON.stringify({
        type: 'generation_error',
        streamId,
        message: error.message,
        timestamp: Date.now()
      }));

      stream.metadata.status = 'failed';
      stream.metadata.error = error.message;
    }
  }

  /**
   * Handle generation cancellation
   * @param {WebSocket} ws - Client WebSocket
   * @param {string} streamId - Stream identifier
   */
  handleCancelGeneration(ws, streamId) {
    const stream = this.activeStreams.get(streamId);
    if (stream) {
      stream.metadata.status = 'cancelled';
      stream.metadata.cancelledAt = Date.now();

      ws.send(JSON.stringify({
        type: 'generation_cancelled',
        streamId,
        timestamp: Date.now()
      }));

      logger.info(`Generation cancelled for stream ${streamId}`);
    }
  }

  /**
   * Forward request to appropriate model
   * @param {string} streamId - Stream identifier
   * @param {Object} payload - Generation parameters
   * @returns {Promise<Object>} Model response stream
   */
  async forwardToModel(streamId, payload) {
    // In a real implementation, this would use the model router
    // For now, we'll simulate by calling the actual model runtime
    const modelUrl = process.env.GEMMA_4B_URL || 'http://localhost:8080';

    const response = await fetch(`${modelUrl}/v1/completions`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({
        model: "gemma-4b-it",
        prompt: payload.prompt,
        max_tokens: payload.max_tokens || 512,
        temperature: payload.temperature || 0.7,
        top_p: payload.top_p || 0.9,
        stream: true
      })
    });

    if (!response.ok) {
      throw new Error(`Model service error: ${response.status}`);
    }

    return response.body;
  }

  /**
   * Stream response chunks to client
   * @param {WebSocket} ws - Client WebSocket
   * @param {string} streamId - Stream identifier
   * @param {ReadableStream} modelResponse - Response stream from model
   * @returns {Promise<void>}
   */
  async streamResponseToClient(ws, streamId, modelResponse) {
    const stream = this.activeStreams.get(streamId);
    if (!stream) return;

    // Process the streaming response from the model
    const reader = modelResponse.getReader();
    const decoder = new TextDecoder('utf-8');
    let buffer = '';

    try {
      while (true) {
        const { done, value } = await reader.read();
        if (done) break;

        buffer += decoder.decode(value, { stream: true });
        const lines = buffer.split('\n');
        buffer = lines.pop(); // Keep incomplete line in buffer

        for (const line of lines) {
          if (line.startsWith('data: ')) {
            const data = line.substring(5);
            if (data === '[DONE]') {
              return;
            }

            try {
              const parsed = JSON.parse(data);
              const token = parsed.choices?.[0]?.text || '';

              if (token) {
                // Update token count
                stream.metadata.tokenCount += 1;

                // Send token to client
                ws.send(JSON.stringify({
                  type: 'token',
                  streamId,
                  token,
                  tokenCount: stream.metadata.tokenCount,
                  timestamp: Date.now()
                }));
              }

              // Check for completion
              if (parsed.choices?.[0]?.finish_reason) {
                return;
              }
            } catch (e) {
              // Skip malformed JSON
            }
          }
        }
      }
    } finally {
      reader.releaseLock();
    }
  }

  /**
   * Broadcast message to all clients in a stream
   * @param {string} streamId - Stream identifier
   * @param {Object} message - Message to broadcast
   */
  broadcastToStream(streamId, message) {
    const stream = this.activeStreams.get(streamId);
    if (!stream) return;

    const messageStr = JSON.stringify(message);
    stream.clients.forEach((client) => {
      if (client.readyState === WebSocket.OPEN) {
        client.send(messageStr);
      }
    });
  }

  /**
   * Get statistics for active streams
   * @returns {Object} Streaming statistics
   */
  getStatistics() {
    const stats = {
      totalStreams: this.activeStreams.size,
      activeStreams: 0,
      completedStreams: 0,
      failedStreams: 0,
      totalClients: 0,
      streams: []
    };

    for (const [streamId, stream] of this.activeStreams.entries()) {
      const clientCount = stream.clients.size;
      stats.totalClients += clientCount;

      if (stream.metadata.status === 'generating') {
        stats.activeStreams++;
      } else if (stream.metadata.status === 'completed') {
        stats.completedStreams++;
      } else if (stream.metadata.status === 'failed') {
        stats.failedStreams++;
      }

      stats.streams.push({
        id: streamId,
        clientCount,
        status: stream.metadata.status,
        createdAt: stream.metadata.createdAt,
        tokenCount: stream.metadata.tokenCount || 0,
        durationMs: stream.metadata.completedAt
          ? stream.metadata.completedAt - stream.metadata.startedAt
          : Date.now() - (stream.metadata.startedAt || Date.now())
      });
    }

    return stats;
  }

  /**
   * Cleanup stale streams
   * @param {number} maxAgeMs - Maximum age in milliseconds before cleanup
   */
  cleanupStaleStreams(maxAgeMs = 3600000) { // Default 1 hour
    const now = Date.now();
    let cleaned = 0;

    for (const [streamId, stream] of this.activeStreams.entries()) {
      if (now - stream.metadata.lastActivity > maxAgeMs) {
        // Close all client connections
        stream.clients.forEach((client) => {
          if (client.readyState === WebSocket.OPEN) {
            client.close(4000, 'Stream expired due to inactivity');
          }
        });

        this.activeStreams.delete(streamId);
        cleaned++;
      }
    }

    if (cleaned > 0) {
      logger.info(`Cleaned up ${cleaned} stale streams`);
    }

    return cleaned;
  }
}

module.exports = { StreamingService };