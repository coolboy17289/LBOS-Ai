const express = require('express');
const router = express.Router();
const { authenticateToken } = require('./auth');

// Get model usage statistics
router.get('/', authenticateToken, async (req, res) => {
  try {
    // In a real implementation, this would come from usage tracking
    // For now, we'll return mock data
    const usage = [
      {
        name: 'Gemma 4B',
        type: 'Gemma 4B',
        requestCount: 142,
        avgResponseTime: 1250,
        successRate: 0.98
      },
      {
        name: 'Gemma 5B',
        type: 'Gemma 5B',
        requestCount: 89,
        avgResponseTime: 1800,
        successRate: 0.95
      },
      {
        name: 'Local Model',
        type: 'Local',
        requestCount: 234,
        avgResponseTime: 800,
        successRate: 0.99
      }
    ];
    
    res.json(usage);
  } catch (error) {
    console.error('Error fetching model usage:', error);
    res.status(500).json({ error: 'Failed to fetch model usage' });
  }
});

module.exports = router;
