const express = require('express');
const router = express.Router();
const jwt = require('jsonwebtoken');
const bcrypt = require('bcryptjs');
const { User } = require('../models');

// In a real app, you would have proper user registration and authentication
// For now, we'll simulate a simple token-based auth for internal use

// Mock login endpoint (for development only)
router.post('/login', async (req, res) => {
  try {
    const { username, password } = req.body;

    // In production, validate against database
    // For now, accept any credentials for demo
    if (!username || !password) {
      return res.status(400).json({ error: 'Username and password required' });
    }

    // Create a simple JWT token
    const token = jwt.sign(
      { userId: 1, username },
      process.env.JWT_SECRET || 'dev-secret-key',
      { expiresIn: '24h' }
    );

    res.json({ token, user: { id: 1, username } });
  } catch (error) {
    console.error('Login error:', error);
    res.status(500).json({ error: 'Internal server error' });
  }
});

// Middleware to verify JWT token
const authenticateToken = (req, res, next) => {
  const authHeader = req.headers['authorization'];
  const token = authHeader && authHeader.split(' ')[1];

  if (!token) {
    return res.status(401).json({ error: 'Access token required' });
  }

  jwt.verify(token, process.env.JWT_SECRET || 'dev-secret-key', (err, user) => {
    if (err) {
      return res.status(403).json({ error: 'Invalid or expired token' });
    }
    req.user = user;
    next();
  });
};

router.get('/profile', authenticateToken, (req, res) => {
  res.json({ user: req.user });
});

module.exports = { router, authenticateToken };