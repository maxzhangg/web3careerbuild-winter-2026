const { expect } = require("chai");

describe("SimpleStorage", function () {
  it("stores and updates message", async function () {
    const factory = await ethers.getContractFactory("SimpleStorage");
    const contract = await factory.deploy("hello");
    await contract.waitForDeployment();

    expect(await contract.getMessage()).to.equal("hello");

    const tx = await contract.setMessage("world");
    await tx.wait();

    expect(await contract.getMessage()).to.equal("world");
  });
});
