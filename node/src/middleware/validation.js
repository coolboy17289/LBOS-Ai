const Joi = require('joi');

// Validation schemas
const schemas = {
  // URL ingestion validation
  ingestUrl: Joi.object({
    urls: Joi.array().items(Joi.string().uri().required()).min(1).required(),
    type: Joi.string().valid('youtube', 'web', 'mixed').default('mixed')
  }),

  // Training job validation
  trainModel: Joi.object({
    datasetId: Joi.string().required(),
    config: Joi.object({
      modelType: Joi.string().valid('transformer', 'lstm', 'cnn').default('transformer'),
      layers: Joi.number().integer().min(1).max(24).default(6),
      hiddenSize: Joi.number().integer().min(64).max(2048).default(768),
      attentionHeads: Joi.number().integer().min(1).max(16).default(12),
      learningRate: Joi.number().min(1e-6).max(1e-1).default(5e-5),
      batchSize: Joi.number().integer().min(1).max(512).default(16),
      epochs: Joi.number().integer().min(1).max(100).default(3),
      maxSeqLength: Joi.number().integer().min(32).max(2048).default(512)
    }).default()
  }),

  // Evaluation job validation
  evaluateModel: Joi.object({
    modelId: Joi.string().required(),
    testSetId: Joi.string().required(),
    metrics: Joi.array().items(Joi.string().valid('perplexity', 'accuracy', 'f1', 'bleu', 'rouge')).default(['perplexity', 'accuracy', 'f1'])
  })
};

// Validation middleware
function validate(schemaName) {
  return (req, res, next) => {
    const schema = schemas[schemaName];
    if (!schema) {
      return res.status(500).json({ error: `Validation schema ${schemaName} not found` });
    }

    const { error, value } = schema.validate(req.body, { abortEarly: false });
    if (error) {
      const errors = error.details.map(detail => ({
        field: detail.path.join('.'),
        message: detail.message
      }));
      return res.status(400).json({ error: 'Validation failed', details: errors });
    }

    // Replace req.body with validated value
    req.body = value;
    next();
  };
}

module.exports = { validate };