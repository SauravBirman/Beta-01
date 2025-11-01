const hre = require("hardhat");
const fs = require("fs");
const path = require("path");

async function main() {
  const ReportContract = await hre.ethers.getContractFactory("ReportContract");
  const contract = await ReportContract.deploy();
  await contract.deployed();

  console.log("✅ Contract deployed at:", contract.address);

  // Save ABI + address for backend
  const contractData = {
    address: contract.address,
    abi: JSON.parse(contract.interface.format("json")),
  };

  const abiPath = path.join(__dirname, "../../config/ReportContractABI.json");
  fs.writeFileSync(abiPath, JSON.stringify(contractData, null, 2));

  console.log("ABI and address saved to:", abiPath);
}

main().catch((error) => {
  console.error(error);
  process.exitCode = 1;
});
