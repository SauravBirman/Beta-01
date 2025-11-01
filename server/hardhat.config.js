import "@nomiclabs/hardhat-waffle";
import "dotenv/config";

export default {
  solidity: "0.8.20",
  networks: {
    sepolia: {
      url: process.env.RPC_URL,
      accounts: [process.env.PRIVATE_KEY],
    },
  },
};
