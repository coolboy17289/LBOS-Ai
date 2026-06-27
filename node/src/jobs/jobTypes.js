class IngestionJob {
  constructor(jobId, data) {
    this.jobId = jobId;
    this.data = data;
  }

  toQueueJob() {
    return {
      name: 'ingestion',
      data: {
        jobId: this.jobId,
        ...this.data
      }
    };
  }
}

class TrainingJob {
  constructor(jobId, data) {
    this.jobId = jobId;
    this.data = data;
  }

  toQueueJob() {
    return {
      name: 'training',
      data: {
        jobId: this.jobId,
        ...this.data
      }
    };
  }
}

class EvaluationJob {
  constructor(jobId, data) {
    this.jobId = jobId;
    this.data = data;
  }

  toQueueJob() {
    return {
      name: 'evaluation',
      data: {
        jobId: this.jobId,
        ...this.data
      }
    };
  }
}

module.exports = { IngestionJob, TrainingJob, EvaluationJob };