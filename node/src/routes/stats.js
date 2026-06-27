const express = require('express');
const router = express.Router();
const { authenticateToken } = require('./auth');

// Get system stats
router.get('/', authenticateToken, async (req, res) => {
  try {
    // In a real implementation, these would come from actual system metrics
    // For now, we'll return mock data
    const stats = {
      status: 'online',
      modelsLoaded: 2, // Gemma 4B and 5B
      totalRequests: Math.floor(Math.random() * 1000),
      avgResponseTime: 1200 + Math.random() * 800
    };
    
    res.json(stats);
  } catch (error) {
    console.error('Error fetching stats:', error);
    res.status(500).json({ error: 'Failed to fetch stats' });
  }
});

module.exports = router;
