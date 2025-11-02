const Report = require('../models/reportModel');
const { uploadFile, getFile } = require('../utils/ipfs');
const ethers = require('ethers');
const fs = require('fs');
const path = require('path');
require('dotenv').config();

console.log('RPC_URL:', process.env.RPC_URL);
console.log('PRIVATE_KEY:', process.env.PRIVATE_KEY ? 'loaded' : 'missing');
console.log('CONTRACT_ADDRESS:', process.env.CONTRACT_ADDRESS);


// Example: smart contract setup
const contractJSON = require('../config/ReportContractABI.json');
const contractABI = contractJSON.abi;
const contractAddress = process.env.CONTRACT_ADDRESS;

// provider → connects to blockchain network (testnet or local Hardhat/Alchemy).
// signer → patient wallet/private key for sending transactions.
// contract → ethers.Contract instance to call smart contract functions.


const provider = new ethers.JsonRpcProvider(process.env.RPC_URL);
const signer = new ethers.Wallet(process.env.PRIVATE_KEY, provider);
const contract = new ethers.Contract(
  process.env.CONTRACT_ADDRESS,
  contractABI,
  signer
);

// Upload report
const uploadReport = async (req, res) => {
  try {
    const patientId = req.user.id; // from auth middleware
    const patientAddress = req.user.blockchainAddress; 

    const file = req.file; // multer file
    if (!file) return res.status(400).json({ message: 'No file uploaded' });

    // Upload to IPFS
    const ipfsHash = await uploadFile(file.buffer, file.originalname);

    // Save metadata in MongoDB
    const report = await Report.create({
      patient: patientId,
      fileName: file.originalname,
      symptoms: req.body.symptoms || '',
      ipfsHash,
      permissions: [], // initially no doctors
    });

    // Register report on blockchainnpm install --save-dev @nomiclabs/hardhat-waffle ethereum-waffle @nomiclabs/hardhat-ethers ethers dotenv

    const tx = await contract.registerReport(ipfsHash); // patient is msg.sender automatically
    await tx.wait(); // Wait until transaction is mined

    console.log('Transaction hash:', tx.hash);
    
    res.status(201).json({ success: true, report });
  } catch (err) {
    console.error('Upload report error:', err);
    res.status(500).json({ message: 'Server error' });
  }
};

// Grant access
const grantAccess = async (req, res) => {
  try {
    const { reportId, doctorAddress } = req.body || {};

    if (!reportId || !doctorAddress) {
      return res.status(400).json({ message: 'reportId and doctorAddress are required' });
    }

    // Load report
    const report = await Report.findById(reportId);
    if (!report) return res.status(404).json({ message: 'Report not found' });

    // Ensure authenticated user
    if (!req.user || !req.user.id) return res.status(401).json({ message: 'Authentication required' });

    // Only patient can grant access
    if (report.patient.toString() !== req.user.id.toString()) {
      return res.status(403).json({ message: 'Not authorized' });
    }

    // Perform blockchain update first so DB only reflects success
    try {
      const tx = await contract.grantAccess(report.ipfsHash, doctorAddress);
      await tx.wait();
    } catch (chainErr) {
      console.error('Blockchain grantAccess error:', chainErr);
      return res.status(502).json({ message: 'Blockchain transaction failed', error: chainErr.message || chainErr.toString() });
    }

    // Update MongoDB (store doctor address in permissions if not present)
    if (!report.permissions || !report.permissions.includes(doctorAddress)) {
      report.permissions = report.permissions || [];
      report.permissions.push(doctorAddress);
      await report.save();
    }

    res.json({ success: true, message: 'Access granted', report });
  } catch (err) {
    console.error('Grant access error:', err);
    res.status(500).json({ message: 'Server error' });
  }
};

// Download report
const accessReport = async (req, res) => {
  try {
    const { reportId } = req.params;
    const report = await Report.findById(reportId);
    if (!report) return res.status(404).json({ message: 'Report not found' });

    // Check if user is patient or has permission via smart contract
    const canAccess = await contract.canAccess(report.ipfsHash, req.user.blockchainAddress);
    if (!canAccess) return res.status(403).json({ message: 'Access denied' });

    const fileBuffer = await getFile(report.ipfsHash);
    res.setHeader('Content-Disposition', `attachment; filename=${report.fileName}`);
    // res.send(fileBuffer);
    // Instead of res.send(fileBuffer);
    res.json({ ipfsHash: report.ipfsHash, fileName: report.fileName });

  } catch (err) {
    console.error('Download report error:', err);
    res.status(500).json({ message: 'Server error' });
  }
};

// Fetch all reports for a particular user (patient)
// If :userId is omitted and this is used for `/me`, pass req.user.id
const getReportsByUser = async (req, res) => {
  try {
    // prefer route param, otherwise use authenticated user id
    const { userId } = req.params;
    const targetUserId = userId || req.user?.id;

    if (!targetUserId) return res.status(400).json({ message: 'User id is required' });

    // Find reports where patient equals the provided user id
    const reports = await Report.find({ patient: targetUserId }).sort({ uploadedAt: -1 });

    return res.json({ success: true, count: reports.length, reports });
  } catch (err) {
    console.error('Get reports by user error:', err);
    res.status(500).json({ message: 'Server error' });
  }
};

module.exports = { uploadReport, grantAccess, accessReport, getReportsByUser };
