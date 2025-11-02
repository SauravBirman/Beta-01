const mongoose = require('mongoose');

const userSchema = new mongoose.Schema(
  {
    name: {
      type: String,
      required: [true, 'Name is required'],
      trim: true,
    },
    email: {
      type: String,
      required: [true, 'Email is required'],
      unique: true,
      lowercase: true,
      trim: true,
    },
    password: {
      type: String,
      required: [true, 'Password is required'],
    },
    role: {
      type: String,
      enum: ['patient', 'doctor', 'lab', 'admin'],
      default: 'patient',
    },
    profileImage: {
      type: String, // URL or IPFS hash
      default: '',
    },
    blockchainAddress: {
      type: String, // Optional: Ethereum/Polygon address for proof
      default: '',
    },
    lastLogin: {
      type: Date,
    },
  },
  {
    timestamps: true, // automatically adds createdAt and updatedAt
  }
);

// Optional: method to hide password when returning user
userSchema.methods.toJSON = function () {
  const obj = this.toObject();
  delete obj.password;
  return obj;
};

module.exports = mongoose.model('User', userSchema);
