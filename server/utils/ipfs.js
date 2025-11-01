const { create } = require('ipfs-http-client');

// Connect to public IPFS node or local daemon
const client = create({ url: 'https://ipfs.infura.io:5001/api/v0' });

async function uploadFile(fileBuffer, fileName) {
  try {
    const result = await client.add({ path: fileName, content: fileBuffer });
    // result.cid is the IPFS hash
    return result.cid.toString();
  } catch (err) {
    console.error('IPFS upload error:', err);
    throw err;
  }
}

async function getFile(ipfsHash) {
  try {
    const stream = client.cat(ipfsHash);
    let data = [];
    for await (const chunk of stream) {
      data.push(chunk);
    }
    return Buffer.concat(data);
  } catch (err) {
    console.error('IPFS get file error:', err);
    throw err;
  }
}

module.exports = { uploadFile, getFile };
