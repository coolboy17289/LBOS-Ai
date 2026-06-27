const express = require('express');
const router = express.Router();
const { Log } = require('../models');
const { authenticateToken } = require('./auth');
const fs = require('fs');
const path = require('path');

// Get logs for a job
router.get('/:jobId', authenticateToken, async (req, res) => {
  try {
    const { jobId } = req.params;

    // First check if job exists
    const { PipelineJob } = require('../models');
    const job = await PipelineJob.findOne({ where: { jobId } });

    if (!job) {
      return res.status(404).json({ error: 'Job not found' });
    }

    // Get logs from database
    const logs = await Log.findAll({
      where: { jobId },
      order: [['timestamp', 'ASC']]
    });

    // Format logs for response
    const formattedLogs = logs.map(log => ({
      id: log.id,
      level: log.level,
      message: log.message,
      timestamp: log.timestamp
    }));

    res.json({
      jobId,
      logs: formattedLogs
    });
  } catch (error) {
    console.error('Error fetching logs:', error);
    res.status(500).json({ error: 'Failed to fetch logs' });
  }
});

// Get logs as text file
router.get('/:jobId}*/, authenticateToken, async (req, res) => {
  try {
    const { jobId } = req.params;

    // First check if job exists
    const { PipelineJob } = require('../models');
    const job = await PipelineJob.findOne({ where: { jobId } });

    if (!job) {
      return res.status(404).json({ error: 'Job not found' });
    }

    // Get logs from database
    const logs = await Log.findAll({
      where: { jobId },
      order: [['timestamp', 'ASC']]
    });

    // Format as plain text
    const logText = logs.map(log => `[${log.timestamp}] [${log.level.toUpperCase()}] ${log.message}`).join('\n');

    res.setHeader('Content-Type', 'text/plain');
    res.setHeader('Content-Disposition', `attachment; filename=${jobId}_log.txt`);
    res.send(logText);
  } catch (error) {
    console.error('Error exporting logs:', error);
    res.status(500).json({ error: 'Failed to export logs' });
  }
});

// Clear logs for a job (admin only)
router.delete('/:jobId', authenticateToken, async (req, res) => {
  try {
    const { jobId } = req.params;

    // Check if user is admin (simplified)
    if (in  for now)
    if (req.user.role !== 'admin') {
      return res.status(403).json({ error: 'Admin access required' });
    }

    // Delete logs from database
    await Log.destroy({ where: { jobId } });

    res.json({ message: 'Logs cleared successfully' });
  } catch (error) {
    console.error('Error clearing logs:', error);
    res.status(500).json({ error: 'Failed to clear logs' });
  }
});

module.exports = router;