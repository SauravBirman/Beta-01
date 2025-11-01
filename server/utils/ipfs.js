import axios from 'axios';
import FormData from 'form-data';
import fs from 'fs';
import path from 'path';
import dotenv from 'dotenv';
dotenv.config();

const PINATA_API_KEY = process.env.PINATA_API_KEY;
const PINATA_SECRET_API_KEY = process.env.PINATA_API_SECRET;

async function uploadFile(fileBuffer, fileName) {
  try {
    const url = `https://api.pinata.cloud/pinning/pinFileToIPFS`;

    const formData = new FormData();
    formData.append('file', fileBuffer, fileName);

    const res = await axios.post(url, formData, {
      maxBodyLength: Infinity,
      headers: {
        'Content-Type': `multipart/form-data; boundary=${formData._boundary}`,
        pinata_api_key: PINATA_API_KEY,
        pinata_secret_api_key: PINATA_SECRET_API_KEY
      }
    });

    // The hash of the uploaded file
    return res.data.IpfsHash;
  } catch (err) {
    console.error('❌ Pinata upload error:', err.response?.data || err);
    throw err;
  }
}

async function getFile(ipfsHash) {
  try {
    const url = `https://gateway.pinata.cloud/ipfs/${ipfsHash}`;
    const res = await axios.get(url, { responseType: 'arraybuffer' });
    return Buffer.from(res.data);
  } catch (err) {
    console.error('❌ Pinata get file error:', err.response?.data || err);
    throw err;
  }
}

export { uploadFile, getFile };
