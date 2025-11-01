const express = require('express');
const router = express.Router();
const { registerUser, loginUser, getAllUsers, getUserById } = require('../controllers/userController');
const { protect } = require('../middlewares/authUser');

// POST /api/users/register
router.post('/register', registerUser);

// POST /api/users/login
router.post('/login', loginUser);

// GET /api/users  (protected)
router.get('/', protect, getAllUsers);

// GET /api/users/:id  (protected)
router.get('/:id', protect, getUserById);

module.exports = router;
