// controllers/doctorController.js
const Doctor = require('../models/docModel');
const bcrypt = require('bcryptjs');

const registerDoctor = async (req, res) => {
  try {
    const { name, email, password, blockchainAddress, specialty } = req.body;

    // Validate blockchain address presence and format (EOA)
    if (!blockchainAddress || !/^0x[a-fA-F0-9]{40}$/.test(blockchainAddress)) {
      return res.status(400).json({ message: 'Valid blockchainAddress (EOA) is required and must start with 0x' });
    }

    const normalizedAddress = blockchainAddress.toLowerCase();

    const existing = await Doctor.findOne({ email });
    if (existing) return res.status(400).json({ message: 'Doctor already exists' });

    const hashed = await bcrypt.hash(password, 10);

    const doctor = await Doctor.create({
      name, email, password: hashed, blockchainAddress: normalizedAddress, specialty
    });

    res.status(201).json({ success: true, doctor });
  } catch (err) {
    console.error(err);
    res.status(500).json({ message: 'Server error' });
  }
};

module.exports = { registerDoctor };