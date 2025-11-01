const express = require('express');
const router = express.Router();
const { registerUser, loginUser } = require('../controllers/userController');

// POST /api/users/register
router.post('/register', registerUser);

// POST /api/users/login
router.post('/login', loginUser);

module.exports = router;
