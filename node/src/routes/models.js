const express = require('express');
const router = express.Router();
const { v4: uuidv4 } = require('uuid');
const { Model } = require('../models');
const { authenticateToken } = require('./auth');
const ModelRouter = require('../services/modelRouter');

// Initialize model router
const modelRouter = new ModelRouter();

// Get all models
router.get('/', authenticateToken, async (req, res) => {
  try {
    const models = await Model.findAll({
      order: [['createdAt', 'DESC']]
    });

    res.json(models.map(model => ({
      id: model.id,
      modelId: model.modelId,
      name: model.name,
      version: model.version,
      status: model.status,
      accuracy: model.accuracy,
      loss: model.loss,
      createdAt: model.createdAt,
      updatedAt: model.updatedAt
    })));
  } catch (error) {
    console.error('Error fetching models:', error);
    res.status(500).json({ error: 'Failed to fetch models' });
  }
});

// Get specific model
router.get('/:modelId', authenticateToken, async (req, res) => {
  try {
    const { modelId } = req.params;

    const model = await Model.findOne({ where: { modelId } });

    if (!model) {
      return res.status(404).json({ error: 'Model not found' });
    }

    res.json({
      id: model.id,
      modelId: model.modelId,
      name: model.name,
      version: model.version,
      status: model.status,
      accuracy: model.accuracy,
      loss: model.loss,
      config: model.config ? JSON.parse(model.config) : null,
      createdAt: model.createdAt,
      updatedAt: model.updatedAt
    });
  } catch (error) {
    console.error('Error fetching model:', error);
    res.status(500).json({ error: 'Failed to fetch model' });
  }
});

// Delete model
router.delete('/:modelId', authenticateToken, async (req, res) => {
  try {
    const { modelId } = req.params;

    const model = await Model.findOne({ where: { modelId } });

    if (!model) {
      return res.status(404).json({ error: 'Model not found' });
    }

    await model.destroy();

    res.json({ message: 'Model deleted successfully' });
  } catch (error) {
    console.error('Error deleting model:', error);
    res.status(500).json({ error: 'Failed to delete model' });
  }
});

// Chat endpoint
router.post('/chat', authenticateToken, async (req, res) => {
  try {
    const { message, model } = req.body;
    
    if (!message) {
      return res.status(400).json({ error: 'Message is required' });
    }
    
    // Prepare request for model router
    const modelRequest = {
      id: uuidv4(),
      prompt: message,
      max_tokens: 512,
      temperature: 0.7,
      top_p: 0.9,
      stream: false
    };
    
    // If a specific model is requested, we could override the routing here
    // For now, we'll let the model router decide based on the message content
    // In a more advanced implementation, we could pass model preference to the router
    
    // Route the request to the appropriate model
    const response = await modelRouter.routeRequest(modelRequest, {});
    
    // Extract the response text
    let responseText = '';
    if (response.choices && response.choices.length > 0) {
      responseText = response.choices[0].text;
    }
    
    res.json({
      response: responseText,
      modelUsed: response.metadata ? response.metadata.modelUsed : 'unknown'
    });
  } catch (error) {
    console.error('Error in chat endpoint:', error);
    res.status(500).json({ error: 'Failed to process chat request' });
  }
});

// Available models endpoint (for frontend)
router.get('/available', authenticateToken, async (req, res) => {
  try {
    // In a real implementation, this would check which models are actually loaded/available
    // For now, we'll return the configured models from the model router
    const availableModels = Object.keys(modelRouter.models).map(key => {
      const model = modelRouter.models[key];
      return {
        id: key,
        name: model.name || key,
        size: model.maxTokens // Using maxTokens as a rough size indicator
      };
    });
    
    res.json({ models: availableModels });
  } catch (error) {
    console.error('Error fetching available models:', error);
    res.status(500).json({ error: 'Failed to fetch available models' });
  }
});

module.exports = router;
