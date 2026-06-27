const express = require('express');
const router = express.Router();
const { v4: uuidv4 } = require('uuid');
const { Model } = require('../models');
const { authenticateToken } = require('./auth');

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

module.exports = router;