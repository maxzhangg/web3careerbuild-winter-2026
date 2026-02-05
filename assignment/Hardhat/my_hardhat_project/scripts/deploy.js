const hre = require("hardhat");

async function main() {
  // 1. 获取合约工厂（相当于拿到图纸）
  const Counter = await hre.ethers.getContractFactory("Counter");

  // 2. 开始部署（相当于开始造车）
  const counter = await Counter.deploy();

  // 3. 等待部署完成（等车造好）
  await counter.waitForDeployment();

  // 4. 打印地址
  console.log("合约已部署到:", await counter.getAddress());
}

main().catch((error) => {
  console.error(error);
  process.exitCode = 1;
});