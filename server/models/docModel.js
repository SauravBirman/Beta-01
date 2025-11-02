// models/doctorModel.js
const mongoose = require('mongoose');

const doctorSchema = new mongoose.Schema({
  name: { type: String, required: true },
  email: { type: String, required: true, unique: true },
  password: { type: String, required: true }, // hash using bcrypt
  blockchainAddress: {
    type: String,
    required: true,
    validate: {
      validator: function (v) {
        // basic EOA check: starts with 0x followed by 40 hex chars
        return /^0x[a-fA-F0-9]{40}$/.test(v);
      },
      message: props => `${props.value} is not a valid Ethereum address (expected 0x...)`
    }
  }, // EOA from MetaMask
  specialty: { type: String },
  notifications: [
    {
      patientId: { type: mongoose.Schema.Types.ObjectId, ref: 'User' },
      reportIds: [{ type: mongoose.Schema.Types.ObjectId, ref: 'Report' }],
      createdAt: { type: Date, default: Date.now },
    },
  ],
}, { timestamps: true });

module.exports = mongoose.model('Doctor', doctorSchema);