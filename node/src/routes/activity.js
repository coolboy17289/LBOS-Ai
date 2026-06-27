const express = require('express');
const router = express.Router();
const { authenticateToken } = require('./auth');

// Get recent activity
router.get('/recent', authenticateToken, async (req, res) => {
  try {
    // In a real implementation, this would come from a database or log system
    // For now, we'll return mock data
    const activities = [
      {
        type: 'Model Inquiry',
        description: 'User asked about quantum computing',
        timestamp: new Date(Date.now() - 5 * 60 * 1000).toISOString(), // 5 minutes ago
        modelUsed: 'GEMMA_5B'
      },
      {
        type: 'Code Generation',
        description: 'Generated Python function for factorial calculation',
        timestamp: new Date(Date.now() - 15 * 60 * 1000).toISOString(), // 15 minutes ago
        modelUsed: 'GEMMA_4B'
      },
      {
        type: 'Text Summarization',
        description: 'Summarized a news article about climate change',
        timestamp: new Date(Date.now() - 30 * 60 * 1000).toISOString(), // 30 minutes ago
        modelUsed: 'GEMMA_4B'
      },
      {
        type: 'Creative Writing',
        description: 'Wrote a short poem about artificial intelligence',
        timestamp: new Date(Date.now() - 45 * 60 * 1000).toISOString(), // 45 minutes ago
        modelUsed: 'GEMMA_5B'
      }
    ];
    
    res.json(activities);
  } catch (error) {
    console.error('Error fetching recent activity:', error);
    res.status(500).json({ error: 'Failed to fetch recent activity' });
  }
});

module.exports = router;
