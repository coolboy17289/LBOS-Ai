const express = require('express');
const router = express.Router();
const { v4: uuidv4 } = require('uuid');
const { PipelineJob } = require('../models');
const { IngestionJob, TrainingJob, EvaluationJob } = require('../jobs/jobTypes');
const { JobProcessor } = require('../jobs/jobProcessor');
const { validateJobInput } = require('../middleware/validation');

// Middleware to authenticate token
const authenticateToken = (req, res, next) => {
  const authHeader = req.headers['authorization'];
  const token = authHeader && authHeader.split(' ')[1];
  if (!token) return res.status(401).json({ error: 'Access token required' });

  jwt.verify(token, process.env.JWT_SECRET || 'dev-secret-key', (err, user) => {
    if (err) return res.status(403).json({ error: 'Invalid token' });
    req.user = user;
    next();
  });
};

const jwt = require('jsonwebtoken');

// Ingest URL endpoint
router.post('/ingest', authenticateToken, async (req, res) => {
  try {
    const { urls, type = 'mixed' } = req.body;

    if (!urls || !Array.isArray(urls) || urls.length === 0) {
      return res.status(400).json({ error: 'URLs array is required' });
    }

    // Validate each URL
    for (const url of urls) {
      if (!/^https?:\/\//i.test(url)) {
        return res.status(400).json({ error: `Invalid URL: ${url}` });
      }
    }

    // Create job record
    const jobId = uuidv4();
    await PipelineJob.create({
      jobId,
      type: 'ingestion',
      status: 'queued',
      progress: 0,
      inputData: JSON.stringify({ urls, type }),
      createdBy: req.user.userId
    });

    // Add to queue
    const job = new IngestionJob(jobId, { urls, type });
    await JobProcessor.queueManager.queues.get('ingestion').add(job.toQueueJob());

    res.status(202).json({
      jobId,
      message: 'Ingestion job queued successfully',
      status: 'queued'
    });
  } catch (error) {
    console.error('Error creating ingestion job:', error);
    res.status(500).json({ error: 'Failed to create ingestion job' });
  }
});

// Start training endpoint
router.post('/train', authenticateToken, async (req, res) => {
  try {
    const { datasetId, config } = req.body;

    if (!datasetId) {
      return res.status(400).json({ error: 'Dataset ID is required' });
    }

    // Create job record
    const jobId = uuidv4();
    await PipelineJob.create({
      jobId,
      type: 'training',
      status: 'queued',
      progress: 0,
      inputData: JSON.stringify({ datasetId, config }),
      createdBy: req.user.userId
    });

    // Add to queue
    const job = new TrainingJob(jobId, { datasetId, config });
    await JobProcessor.queueManager.queues.get('training').add(job.toQueueJob());

    res.status(202).json({
      jobId,
      message: 'Training job queued successfully',
      status: 'queued'
    });
  } catch (error) {
    console.error('Error creating training job:', error);
    res.status(500).json({ error: 'Failed to create training job' });
  }
});

// Start evaluation endpoint
router.post('/evaluate', authenticateToken, async (req, res) => {
  try {
    const { modelId, testSetId } = req.body;

    if (!modelId || !testSetId) {
      return res.status(400).json({ error: 'Model ID and Test Set ID are required' });
    }

    // Create job record
    const jobId = uuidv4();
    await PipelineJob.create({
      jobId,
      type: 'evaluation',
      status: 'queued',
      progress: 0,
      inputData: JSON.stringify({ modelId, testSetId }),
      createdBy: req.user.userId
    });

    // Add to queue
    const job = new EvaluationJob(jobId, { modelId, testSetId });
    await JobProcessor.queueManager.queues.get('evaluation').add(job.toQueueJob());

    res.status(202).json({
      jobId,
      message: 'Evaluation job queued successfully',
      status: 'queued'
    });
  } catch (error) {
    console.error('Error creating evaluation job:', error);
    res.status(500).json({ error: 'Failed to create evaluation job' });
  }
});

// Get job status
router.get('/:jobId', authenticateToken, async (req, res) => {
  try {
    const { jobId } = req.params;

    const job = await PipelineJob.findOne({ where: { jobId } });

    if (!job) {
      return res.status(404).json({ error: 'Job not found' });
    }

    res.json({
      jobId: job.jobId,
      type: job.type,
      status: job.status,
      progress: job.progress,
      result: job.result ? JSON.parse(job.result) : null,
      createdAt: job.createdAt,
      updatedAt: job.updatedAt
    });
  } catch (error) {
    console.error('Error fetching job status:', error);
    res.status(500).json({ error: 'Failed to fetch job status' });
  }
});

// Get all jobs (with pagination)
router.get('/', authenticateToken, async (req, res) => {
  try {
    const { page = 1, limit = 10, status, type } = req.query;
    const offset = (parseInt(page) - 1) * parseInt(limit);

    const where = {};
    if (status) where.status = status;
    if (type) where.type = type;

    const { count, rows } = await PipelineJob.findAndCountAll({
      where,
      order: [['createdAt', 'DESC']],
      limit: parseInt(limit),
      offset
    });

    res.json({
      jobs: rows.map(job => ({
        jobId: job.jobId,
        type: job.type,
        status: job.status,
        progress: job.progress,
        createdAt: job.createdAt,
        updatedAt: job.updatedAt
      })),
      pagination: {
        total: count,
        page: parseInt(page),
        limit: parseInt(limit),
        pages: Math.ceil(count / parseInt(limit))
      }
    });
  } catch (error) {
    console.error('Error fetching jobs:', error);
    res.status(500).json({ error: 'Failed to fetch jobs' });
  }
});

// Cancel job
router.delete('/:jobId', authenticateToken, async (req, res) => {
  try {
    const { jobId } = req.params;

    const job = await PipelineJob.findOne({ where: { jobId } });

    if (!job) {
      return res.status(404).json({ error: 'Job not found' });
    }

    if (job.status === 'completed' || job.status === 'failed') {
      return res.status(400).json({ error: 'Cannot cancel completed or failed job' });
    }

    // Update job status
    await job.update({ status: 'cancelled' });

    // TODO: Remove from queue if still queued
    // This would require checking the queue and removing the job

    res.json({
      jobId,
      message: 'Job cancelled successfully',
      status: 'cancelled'
    });
  } catch (error) {
    console.error('Error cancelling job:', error);
    res.status(500).json({ error: 'Failed to cancel job' });
  }
});

module.exports = router;