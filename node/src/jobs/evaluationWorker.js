const { PythonShell } = require('python-shell');
const path = require('path');
const fs = require('fs');
const { v4: uuidv4 } = require('uuid');
const { PipelineJob } = require('../models');

class EvaluationWorker {
  async process(jobData) {
    const jobId = jobData.jobId || uuidv4();
    const modelId = jobData.modelId;
    const testSetId = jobData.testSetId;

    try {
      // Update job status
      await PipelineJob.update(
        { status: 'processing', progress: 5 },
        { where: { jobId } }
      );

      // Prepare Python script arguments
      const scriptPath = path.join(__dirname, '..', '..', '..', 'src', 'python', 'lbos_ai', 'eval', 'evaluator.py');
      const scriptArgs = [
        modelId,
        testSetId,
        jobId
      ];

      // Run Python script
      return new Promise((resolve, reject) => {
        PythonShell.run(scriptPath, {
          mode: 'text',
          pythonOptions: ['-u'], // unbuffered output
          args: scriptArgs
        }, (err, results) => {
          if (err) {
            console.error(`Evaluation failed for job ${jobId}:`, err);
            reject(err);
            return;
          }

          // Parse result (should be JSON with evaluation metrics)
          const result = JSON.parse(results[0]);

          // Update job as completed
          PipelineJob.update(
            { status: 'completed', progress: 100, result: JSON.stringify(result) },
            { where: { jobId } }
          );

          resolve(result);
        });
      });
    } catch (error) {
      console.error(`Error in evaluation worker for job ${jobId}:`, error);
      throw error;
    }
  }
}

module.exports = { EvaluationWorker };