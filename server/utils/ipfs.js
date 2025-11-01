let client;

async function getClient() {
  if (!client) {
    const { create } = await import('ipfs-http-client');
    client = create({ url: 'https://ipfs.infura.io:5001/api/v0' });
  }
  return client;
}

async function uploadFile(fileBuffer, fileName) {
  try {
    const ipfs = await getClient();
    const result = await ipfs.add({ path: fileName, content: fileBuffer });
    return result.cid.toString();
  } catch (err) {
    console.error('❌ IPFS upload error:', err);
    throw err;
  }
}

async function getFile(ipfsHash) {
  try {
    const ipfs = await getClient();
    const stream = ipfs.cat(ipfsHash);
    let data = [];
    for await (const chunk of stream) {
      data.push(chunk);
    }
    return Buffer.concat(data);
  } catch (err) {
    console.error('❌ IPFS get file error:', err);
    throw err;
  }
}

module.exports = { uploadFile, getFile };
