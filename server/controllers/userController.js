const User = require('../models/userModel');
const bcrypt = require('bcrypt');
const jwt = require('jsonwebtoken');
const { JWT_SECRET, JWT_EXPIRES_IN } = require('../config/app');

const registerUser = async (req, res) => {
  try {
    const { name, email, password } = req.body;
    if(!name || !email || !password){
        return res.json({success: false , message: "Details not filled"});
    }

    // Check if user already exists
    const existingUser = await User.findOne({ email });
    if (existingUser) return res.status(400).json({ message: 'User already exists' });

    // Hash password
    const salt = await bcrypt.genSalt(10);
    const hash_password = await bcrypt.hash(password, salt);

    let createdUser = await userModel.create({
        name,
        email,
        password: hash_password
    })


    res.status(201).json({
      success: true,
      data: {
        id: user._id,
        name: user.name,
        email: user.email,
      },
    });

    const token = jwt.sign({id: createdUser._id}, JWT_SECRET);
    // res.cookie("Token", token);
    res.json({success: true , token , user: {name: createdUser.name}});

  } catch (error) {
    console.error('Register error:', error);
    res.status(500).json({ message: 'Server error' });
  }
};


const loginUser = async (req, res) => {
  try {
    const { email, password } = req.body;

    if(!email || !password){
        return res.json({success: false , message: "Details not filled"});
    }

    const user = await User.findOne({ email });
    if (!user) return res.status(404).json({ message: 'Invalid email or password' });

    const isMatch = await bcrypt.compare(password, user.password);
    if (!isMatch) return res.status(401).json({ message: 'Invalid email or password' });

    // Generate JWT token
    const token = jwt.sign({ id: user._id }, JWT_SECRET, {
      expiresIn: JWT_EXPIRES_IN,
    });

    res.json({
      success: true,
      token,
      user: { id: user._id, name: user.name, email: user.email },
    });
  } catch (error) {
    console.error('Login error:', error);
    res.status(500).json({ message: 'Server error' });
  }
};



module.exports = { registerUser, loginUser };