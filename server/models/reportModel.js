const mongoose = require('mongoose');

const reportSchema = new mongoose.Schema({
  patient: { type: mongoose.Schema.Types.ObjectId, ref: 'User', required: true },
  fileName: { type: String, required: true },
  ipfsHash: { type: String, required: true },
  uploadedAt: { type: Date, default: Date.now },
  permissions: [{ type: mongoose.Schema.Types.ObjectId, ref: 'User' }], // doctors allowed
  description: { type: String, default: '' },
}, { timestamps: true });

module.exports = mongoose.model('Report', reportSchema);
