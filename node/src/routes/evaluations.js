const express = require('express');
const router = express.Router();
const { Evaluation } = require('../models');
const { authenticateToken } = require('./auth');

// Get all evaluations
router.get('/', authenticateToken, async (req, res) => {
  try {
    const { page = 1, limit = 10, modelId } = req.query;
    const offset = (parseInt(page) - 1) * parseInt(limit);

    const where = {};
    if (modelId) where.modelId = modelId;

    const { count, rows } = await Evaluation.findAndCountAll({
      where,
      order: [['createdAt', 'DESC']],
      limit: parseInt(limit),
      offset
    });

    res.json({
      evaluations: rows.map(eval => ({
        id: eval.id,
        evaluationId: eval.evaluationId,
        modelId: eval.modelId,
        testSetId: eval.testSetId,
        metrics: eval.metrics ? JSON.parse(eval.metrics) : null,
        status: eval.status,
        createdAt: eval.createdAt,
        updatedAt: eval.updatedAt
      })),
      pagination: {
        total: count,
        page: parseInt(page),
        limit: parseInt(limit),
        pages: Math.ceil(count / parseInt(limit))
      }
    });
  } catch (error) {
    console.error('Error fetching evaluations:', error);
    res.status(500).json({ error: 'Failed to fetch evaluations' });
  }
});

// Get specific evaluation
router.get('/:evaluationId', authenticateToken, async (req, res) => {
  try {
    const { evaluationId } = req.params;

    const evaluation = await Evaluation.findOne({ where: { evaluationId } });

    if (!evaluation) {
      return res.status(404).json({ error: 'Evaluation not found' });
    }

    res.json({
      id: evaluation.id,
      evaluationId: evaluation.evaluationId,
      modelId: evaluation.modelId,
      testSetId: evaluation.testSetId,
      metrics: evaluation.metrics ? JSON.parse(evaluation.metrics) : null,
      status: evaluation.status,
      reportUrl: evaluation.reportUrl,
      createdAt: evaluation.createdAt,
      updatedAt: evaluation.updatedAt
    });
  } catch (error) {
    console.error('Error fetching evaluation:', error);
    res.status(500).json({ error: 'Failed to fetch evaluation' });
  }
});

// Delete evaluation
router.delete('/:evaluationId', authenticateToken, async (req, res) => {
  try {
    const { evaluationId } = req.params;

    const evaluation = await Evaluation.findOne({ where: { evaluationId } });

    if (!evaluation) {
      return res.status(404).json({ error: 'Evaluation not found' });
    }

    await evaluation.destroy();

    res.json({ message: 'Evaluation deleted successfully' });
  } catch (error) {
    console.error('Error deleting evaluation:', error);
    res.status(500).json({ error: 'Failed to delete evaluation' });
  }
});

module.exports = router;