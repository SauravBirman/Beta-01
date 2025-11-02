// controllers/patientController.js
const Doctor = require('../models/docModel');
const Report = require('../models/reportModel');

const ethers = require('ethers');
const contractJSON = require('../config/ReportContractABI.json');
const contractABI = contractJSON.abi;
const contractAddress = process.env.CONTRACT_ADDRESS;

// Initialize blockchain provider / signer / contract (uses env vars)
const provider = new ethers.JsonRpcProvider(process.env.RPC_URL);
const signer = new ethers.Wallet(process.env.PRIVATE_KEY, provider);
const contract = new ethers.Contract(contractAddress, contractABI, signer);


const selectDoctor = async (req, res) => {
  try {
    const { doctorId } = req.body;
    const patientId = req.user.id;

    const doctor = await Doctor.findById(doctorId);
    if (!doctor) return res.status(404).json({ message: 'Doctor not found' });

    // Get latest 3 reports of patient
    const reports = await Report.find({ patient: patientId })
      .sort({ uploadedAt: -1 })
      .limit(3);

    // Grant access on blockchain for each report
    for (let r of reports) {
      const tx = await contract.grantAccess(r.ipfsHash, doctor.blockchainAddress);
      await tx.wait();
    }

    // Save notification for doctor
    doctor.notifications.push({
      patientId,
      reportIds: reports.map(r => r._id),
    });
    await doctor.save();

    res.status(200).json({ success: true, message: 'Doctor notified', reports });
  } catch (err) {
    console.error(err);
    res.status(500).json({ message: 'Server error' });
  }
};


module.exports = {
  selectDoctor,
};