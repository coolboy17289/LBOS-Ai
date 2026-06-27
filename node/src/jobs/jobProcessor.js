const { BullMQWorker } = require('bullmq');
const { QueueManager } = require('./queueManager');
const { IngestionWorker } = require('./ingestionWorker');
const { TrainingWorker } = require('./trainingWorker');
const { EvaluationWorker } = require('./evaluationWorker');
const { PipelineJob } = require('../models');

class JobProcessor {
  constructor() {
    this.queueManager = QueueManager;
    this.workers = new Map();
  }

  async initialize() {
    await this.queueManager.initialize();

    // Set up workers for each queue type
    this.setupIngestionWorker();
    this.setupTrainingWorker();
    this.setupEvaluationWorker();
  }

  setupIngestionWorker() {
    const worker = new BullMQWorker('ingestion', async (job) => {
      const ingestionWorker = new IngestionWorker();
      return await ingestionWorker.process(job.data);
    }, {
      connection: this.queueManager.connection
    });

    this.workers.set('ingestion', worker);
    this.setupWorkerEvents(worker, 'ingestion');
  }

  setupTrainingWorker() {
    const worker = new BullMQWorker('training', async (job) => {
      const trainingWorker = new TrainingWorker();
      return await trainingWorker.process(job.data);
    }, {
      connection: this.queueManager.connection
    });

    this.workers.set('training', worker);
    this.setupWorkerEvents(worker, 'training');
  }

  setupEvaluationWorker() {
    const worker = new BullMQWorker('evaluation', async (job) => {
      const evaluationWorker = new EvaluationWorker();
      return await evaluationWorker.process(job.data);
    }, {
      connection: this.queueManager.connection
    });

    this.workers.set('evaluation', worker);
    this.setupWorkerEvents(worker, 'evaluation');
  }

  setupWorkerEvents(worker, queueName) {
    worker.on('completed', (jobId) => {
      console.log(`Job ${jobId} completed successfully in queue ${queueName}`);
    });

    worker.on('failed', (job, err) => {
      console.error(`Job ${job.id} failed in queue ${queueName}:`, err.message);
    });

    worker.on('error', (err) => {
      console.error(`Worker error in queue ${queueName}:`, err);
    });
  }

  async shutdown() {
    // Close all workers
    for (const [name, worker] of this.workers) {
      await worker.close();
      console.log(`Worker ${name} closed`);
    }

    // Close queue manager
    await this.queueManager.shutdown();
  }
}

module.exports = { JobProcessor: new JobProcessor() };