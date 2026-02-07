const hre = require("hardhat");

async function main() {
  const initialMessage = "Hello Sepolia";

  const factory = await hre.ethers.getContractFactory("SimpleStorage");
  const contract = await factory.deploy(initialMessage);
  await contract.waitForDeployment();

  const address = await contract.getAddress();
  console.log("SimpleStorage deployed to:", address);
}

main().catch((error) => {
  console.error(error);
  process.exitCode = 1;
});
