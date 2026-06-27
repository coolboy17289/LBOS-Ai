const { Worker, Queue, WorkerOptions } = require('bullmq');
const { PipelineJob } = require('../models');
const { IngestionWorker } = require('./ingestionWorker');
const { TrainingWorker } = require('./trainingWorker');
const { EvaluationWorker } = require('./evaluationWorker');
const { publishJobProgress } = require('../ws/websocket');

class QueueManager {
  constructor() {
    this.queues = new Map();
    this.workers = new Map();
    this.connection = {
      host: process.env.REDIS_HOST || 'localhost',
      port: process.env.REDIS_PORT || 6379,
      password: process.env.REDIS_PASSWORD || null
    };
  }

  initializeQueues() {
    // Create queues
    this.queues.set('ingestion', new Queue('ingestion', { connection: this.connection }));
    this.queues.set('training', new Queue('training', { connection: this.connection }));
    this.queues.set('evaluation', new Queue('evaluation', { connection: this.connection }));

    // Create workers
    this.workers.set('ingestion', new Worker(
      'ingestion',
      async (job) => {
        const ingestionWorker = new IngestionWorker();
        return await ingestionWorker.process(job.data);
      },
      { connection: this.connection, concurrency: 2 }
    ));

    this.workers.set('training', new Worker(
      'training',
      async (job) => {
        const trainingWorker = new TrainingWorker();
        return await trainingWorker.process(job.data);
      },
      { connection: this.connection, concurrency: 1 } // Only one training job at a time per GPU
    ));

    this.workers.set('evaluation', new Worker(
      'evaluation',
      async (job) => {
        const evaluationWorker = new EvaluationWorker();
        return await evaluationWorker.process(job.data);
      },
      { connection: this.connection, concurrency: 2 }
    ));

    // Set up job progress listeners
    this.setupProgressListeners();
  }

  setupProgressListeners() {
    // Listen for progress updates from workers
    this.workers.forEach((worker, queueName) => {
      worker.on('progress', (jobId, progress) => {
        // Update job in database
        PipelineJob.update(
          { progress: progress.percentage || 0, status: 'processing' },
          { where: { jobId } }
        );

        // Publish to WebSocket
        publishJobProgress(jobId, {
          status: 'processing',
          progress: progress.percentage || 0,
          message: progress.message || `Processing step: ${progress.step || 'unknown'}`
        });
      });

      worker.on('completed', (jobId, result) => {
        // Update job in database
        PipelineJob.update(
          { status: 'completed', progress: 100, result: JSON.stringify(result) },
          { where: { jobId } }
        );

        // Publish to WebSocket
        publishJobProgress(jobId, {
          status: 'completed',
          progress: 100,
          message: 'Job completed successfully',
          result
        });
      });

      worker.on('failed', (jobId, error) => {
        // Update job in database
        PipelineJob.update(
          { status: 'failed', errorMessage: error.message || 'Unknown error' },
          { where: { jobId } }
        );

        // Publish to WebSocket
        publishJobProgress(jobId, {
          status: 'failed',
          progress: 0,
          message: `Job failed: ${error.message || 'Unknown error'}`
        });
      });
    });
  }

  async addJob(queueName, jobData, options = {}) {
    const queue = this.queues.get(queueName);
    if (!queue) {
      throw new Error(`Queue ${queueName} not initialized`);
    }

    const job = await queue.add(jobData.jobType || 'default', jobData, options);

    // Create job record in database
    await PipelineJob.create({
      jobId: job.id,
      jobType: jobData.jobType || 'default',
      status: 'queued',
      progress: 0,
      inputData: JSON.stringify(jobData),
      createdAt: new Date()
    });

    return job;
  }

  async getJobStatus(jobId) {
    return await PipelineJob.findOne({ where: { jobId } });
  }

  async cancelJob(jobId) {
    // Find which queue the job belongs to
    const job = await PipelineJob.findOne({ where: { jobId } });
    if (!job) {
      throw new Error('Job not found');
    }

    const queueNameMap = {
      ingestion: 'ingestion',
      training: 'training',
      evaluation: 'evaluation'
    };

    const queueName = queueNameMap[job.jobType] || 'ingestion';
    const queue = this.queues.get(queueName);
    if (!queue) {
      throw new Error(`Queue ${queueName} not found`);
    }

    // Cancel the job
    await queue.remove(jobId);

    // Update job status
    await PipelineJob.update(
      { status: 'cancelled' },
      { where: { jobId } }
    );

    // Publish to WebSocket
    publishJobProgress(jobId, {
      status: 'cancelled',
      progress: 0,
      message: 'Job cancelled by user'
    });

    return true;
  }

  async shutdown() {
    // Close all workers
    for (const [name, worker] of this.workers) {
      await worker.close();
      console.log(`Worker ${name} closed`);
    }

    // Close all queues
    for (const [name, queue] of this.queues) {
      await queue.close();
      console.log(`Queue ${name} closed`);
    }

    // Close Redis connections
    // Note: BullMQ manages its own connections, but we close explicitly if needed
  }
}

module.exports = { QueueManager: new QueueManager() };