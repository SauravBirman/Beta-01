const express = require('express');
const router = express.Router();
const { analyzeSyndrome } = require('../controllers/syndrome');

// Public endpoint: allow calls with or without Authorization header
router.post('/analyze', analyzeSyndrome);

module.exports = router;