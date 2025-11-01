const jwt = require('jsonwebtoken');
const User = require('../models/userModel');
const { JWT_SECRET } = require('../config/app');

const auth = async (req, res, next) => {
  try {
    // 1. Get token from Authorization header
    const authHeader = req.headers.authorization;
    if (!authHeader || !authHeader.startsWith('Bearer ')) {
      return res.status(401).json({ success: false, message: 'No token provided' });
    }

    const token = authHeader.split(' ')[1];

    // 2. Verify token
    const decoded = jwt.verify(token, JWT_SECRET);

    // 3. Fetch user from DB
    const user = await User.findById(decoded.id).select('-password'); // exclude password
    if (!user) {
      return res.status(401).json({ success: false, message: 'Invalid token' });
    }

    // 4. Attach user to request
    req.user = user;

    // 5. Call next middleware/controller
    next();

  } catch (error) {
    console.error('Auth error:', error);
    res.status(401).json({ success: false, message: 'Unauthorized' });
  }
};

module.exports = auth;
