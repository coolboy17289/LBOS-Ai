const { PythonShell } = require('python-shell');
const path = require('path');
const fs = require('fs');
const { v4: uuidv4 } = require('uuid');
const { PipelineJob } = require('../models');

class IngestionWorker {
  async process(jobData) {
    const jobId = jobData.jobId || uuidv4();
    const url = jobData.url;
    const type = jobData.type || this.detectUrlType(url);

    try {
      // Update job status
      await PipelineJob.update(
        { status: 'processing', progress: 10 },
        { where: { jobId } }
      );

      // Prepare Python script arguments
      let scriptPath;
      let scriptArgs;

      if (type === 'youtube') {
        scriptPath = path.join(__dirname, '..', '..', '..', 'src', 'python', 'lbos_ai', 'data', 'youtube.py');
        scriptArgs = [url, jobId];
      } else if (type === 'web') {
        scriptPath = path.join(__dirname, '..', '..', '..', 'src', 'python', 'lbos_ai', 'data', 'web.py');
        scriptArgs = [url, jobId];
      } else {
        throw new Error(`Unsupported URL type: ${type}`);
      }

      // Ensure output directory exists
      const outputDir = path.join(__dirname, '..', '..', '..', 'data', 'raw');
      if (!fs.existsSync(outputDir)) {
        fs.mkdirSync(outputDir, { recursive: true });
      }

      // Run Python script
      return new Promise((resolve, reject) => {
        PythonShell.run(scriptPath, {
          mode: 'text',
          pythonOptions: ['-u'], // unbuffered output
          args: scriptArgs
        }, (err, results) => {
          if (err) {
            console.error(`Ingestion failed for job ${jobId}:`, err);
            reject(err);
            return;
          }

          // Parse result
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
      console.error(`Error in ingestion worker for job ${jobId}:`, error);
      throw error;
    }
  }

  detectUrlType(url) {
    const youtubeRegex = /^(https?:\/\/)?(www\.)?(youtube\.com|youtu\.?be)\/.+$/;
    return youtubeRegex.test(url) ? 'youtube' : 'web';
  }
}

module.exports = { IngestionWorker };