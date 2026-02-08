# 🏗 Scaffold-ETH 2

<h4 align="center">
  <a href="https://docs.scaffoldeth.io">Documentation</a> |
  <a href="https://scaffoldeth.io">Website</a>
</h4>

🧪 An open-source, up-to-date toolkit for building decentralized applications (dapps) on the Ethereum blockchain. It's designed to make it easier for developers to create and deploy smart contracts and build user interfaces that interact with those contracts.

⚙️ Built using NextJS, RainbowKit, Hardhat, Wagmi, Viem, and Typescript.

- ✅ **Contract Hot Reload**: Your frontend auto-adapts to your smart contract as you edit it.
- 🪝 **[Custom hooks](https://docs.scaffoldeth.io/hooks/)**: Collection of React hooks wrapper around [wagmi](https://wagmi.sh/) to simplify interactions with smart contracts with typescript autocompletion.
- 🧱 [**Components**](https://docs.scaffoldeth.io/components/): Collection of common web3 components to quickly build your frontend.
- 🔥 **Burner Wallet & Local Faucet**: Quickly test your application with a burner wallet and local faucet.
- 🔐 **Integration with Wallet Providers**: Connect to different wallet providers and interact with the Ethereum network.

![Debug Contracts tab](https://github.com/scaffold-eth/scaffold-eth-2/assets/55535804/b237af0c-5027-4849-a5c1-2e31495cccb1)

## Requirements

Before you begin, you need to install the following tools:

- [Node (>= v20.18.3)](https://nodejs.org/en/download/)
- Yarn ([v1](https://classic.yarnpkg.com/en/docs/install/) or [v2+](https://yarnpkg.com/getting-started/install))
- [Git](https://git-scm.com/downloads)

# 🚩 Challenge: 🎲 Dice Game

![readme](https://raw.githubusercontent.com/scaffold-eth/se-2-challenges/challenge-dice-game/extension/packages/nextjs/public/hero.png)

> 🎰 Randomness is tricky on a public deterministic blockchain. The block hash is an easy to use, but very weak form of randomness. This challenge will give you an example of a contract using the block hash to create random numbers. This randomness is exploitable. Other, stronger forms of randomness include commit/reveal schemes, oracles, or VRF from Chainlink.

> 💬 Dice Game is a contract that allows users to roll the dice to try and win the prize. If players roll either a 0, 1, 2, 3, 4 or 5 they will win the current prize amount. The initial prize is 10% of the contract's balance, which starts out at .05 Eth.

> 🧤 Every time a player rolls the dice, they are required to send .002 Eth. 40 percent of this value is added to the current prize amount while the other 60 percent stays in the contract to fund future prizes. Once a prize is won, the new prize amount is set to 10% of the total balance of the DiceGame contract.

> 🧨 Your job is to attack the Dice Game contract! You will create a new contract that will predict the randomness ahead of time and only roll the dice when you're guaranteed to be a winner!

> 💬 Meet other builders working on this challenge and get help in the [Challenge telegram](https://t.me/+3StA0aBSArFjNjUx)!

---

## Checkpoint 0: 📦 Environment 📚

> Start your local network (a blockchain emulator in your computer):

```sh
yarn chain
```

> in a second terminal window, 🛰 deploy your contract (locally):

```sh
yarn deploy
```

> in a third terminal window, start your 📱 frontend:

```sh
yarn start
```

📱 Open http://localhost:3000 to see the app.

> 👩‍💻 Rerun `yarn deploy --reset` whenever you want to deploy new contracts to the frontend, update your current contracts with changes, or re-deploy it to get a fresh contract address.

---

⚠️ We have disabled AI in Cursor and VSCode and highly suggest that you do not enable it so you can focus on the challenge, do everything by yourself, and hence better understand and remember things. If you are using another IDE, please disable AI yourself.

🔧 If you are a vibe-coder and don't care about understanding the syntax of the code used and just want to understand the general takeaways, you can re-enable AI by:
- Cursor: remove `*` from `.cursorignore` file
- VSCode: set `chat.disableAIFeatures` to `false` in `.vscode/settings.json` file

---

## Checkpoint 1: 🎲 Dice Game

🔍 Inspect the code in the `DiceGame.sol` contract in `packages/hardhat/contracts`

🔒 You will not be changing any code in the `DiceGame.sol` contract in this challenge. You will write your own contract to predict the outcome, then only roll the dice when it is favourable.

💸 Grab some funds from the faucet and roll the dice a few times. Watch the balance of the DiceGame contract in the Debug tab. It increases on a failed roll and decreases by the prize amount on a successful roll.

![Faucet](https://github.com/scaffold-eth/se-2-challenges/assets/55535804/e82e3100-20fb-4886-a6bf-4113c3729f53)

### 🥅 Goals

- [ ] Track the solidity code to find out how the DiceGame contract is generating random numbers.
- [ ] Is it possible to predict the random number for any given roll?

---

## Checkpoint 2: 🔑 Rigged Contract

Start by creating a `receive()` function in the `RiggedRoll.sol` contract to allow it to receive ETH. This will allow us to fund the `RiggedRoll` contract from the faucet, which is required for our contract to call `rollTheDice()`.

<details markdown='1'>
<summary>🔎 Hint</summary>

Your rigged contract needs to be able to receive ETH via a plain transfer (no calldata). In Solidity, that’s what `receive()` is for.

<details markdown='1'>
<summary>🎯 Solution</summary>

```solidity
receive() external payable {}
```

</details>
</details>

Add these custom error to the error section in `RiggedRoll.sol`:

```solidity
error NotEnoughETH(uint256 required, uint256 available);
error NotWinningRoll(uint256 roll);
```

Next add a `riggedRoll()` function. This function should predict the randomness of a roll, and if the outcome will be a winner, call `rollTheDice()` on the `DiceGame` contract. Revert with `NotEnoughETH` if the contract doesn't hold the required .002 ETH balance. Revert with `NotWinningRoll` if the calculated roll is not a winning number.

🃏 Predict the outcome by generating your random numbers in the exact same way as the DiceGame contract.

> 📣 Reminder! Calling `rollTheDice()` will fail unless you send a message value of at least .002 Eth! [Here is one example of how to send value with a function call.](https://ethereum.stackexchange.com/questions/6665/call-contract-and-send-value-from-solidity)

🎲 Keep in mind the dice on the frontend is using hexadecimal characters but in the contract we can get by with integers. A,B,C,D,E,F = 10,11,12,13,14,15

❓ If you're struggling to get the exact same random number as the DiceGame contract, try adding some `console.log()` statements in both contracts to help you track the values. These messages will appear in the Hardhat node terminal.

<details markdown='1'>
<summary>🔎 Hint</summary>

To match `DiceGame.sol`, you’ll want to:

- Read the current `nonce` from the `DiceGame` contract
- Use `blockhash(block.number - 1)` as the previous block hash
- Hash exactly the same tuple: `(prevHash, diceGameAddress, nonce)`
- Convert to a roll with `% 16`
- Only call `rollTheDice()` when the roll will be a winner
- Revert with `NotWinningRoll` if not a winning number; This way you never pay for gas unless you are winning
- Revert with `NotEnoughETH` if your contract doesn’t have at least `0.002 ether` to spend

<details markdown='1'>
<summary>🎯 Solution</summary>

```solidity
function riggedRoll() external {
    uint256 required = 0.002 ether;
    uint256 available = address(this).balance;
    if (available < required) revert NotEnoughETH(required, available);

    bytes32 prevHash = blockhash(block.number - 1);
    uint256 nonce = diceGame.nonce();
    bytes32 hash = keccak256(abi.encodePacked(prevHash, address(diceGame), nonce));
    uint256 roll = uint256(hash) % 16;

    // Only roll when we know we’ll win (matches the provided tests)
    if (roll > 5) revert NotWinningRoll(roll);

    diceGame.rollTheDice{value: required}();
}
```

</details>
</details>

🚀 To deploy your RiggedRoll contract, uncomment the appropriate lines in the `01_deploy_riggedRoll.ts` file in `packages/hardhat/deploy` and run `yarn deploy --reset`

💸 You will need to send some funds to your RiggedRoll contract before doing your first roll, you can use the Faucet button at the bottom left of the page.

🐞 Go to the `Debug Contracts` tab and try the `riggedRoll` method inside the `RiggedRoll` contract.

### ⚔️ Side Quest

- [ ] Uncomment the code in `packages/nextjs/app/dice/page.tsx` to show a riggedRoll button and contract balance on the main UI tab. Now you can test your function without switching tabs.
- [ ] Does your riggedRoll function only call `rollTheDice()` when it's going to be a winning roll? What happens when it does call `rollTheDice()`?

![RiggedLosingRoll](https://github.com/scaffold-eth/se-2-challenges/assets/55535804/b6c8d7b4-139b-4f54-a62c-a0c77b3692a3)

### Testing your progress

🔍 Run the following command to check if you implemented the rigged roll logic correctly:

```shell
yarn test --grep "Checkpoint2"
```

✅ Did the tests pass? You can dig into any errors by viewing the tests at `packages/hardhat/test/RiggedRoll.ts`.

---

## Checkpoint 3: 💵 Where's my money?!?

You have beaten the game, but where is your money? Since the RiggedRoll contract is the one calling `rollTheDice()`, that is where the prize money is being sent.

![RiggedRollAddress](https://github.com/scaffold-eth/se-2-challenges/assets/55535804/e9b9d164-2fb1-416a-9c5e-198d15bca0c6)

First, add another custom error to `RiggedRoll.sol`:

```solidity
error InsufficientBalance(uint256 requested, uint256 available);
```

📥 Now create a `withdraw(address _addr, uint256 _amount)` function to allow you to send ETH from RiggedRoll to another address.

Make sure you lock the withdraw function so it can only be called by the owner. The `Ownable` contract is already inherited so you have access to the `onlyOwner` modifier.

![WithdrawOnlyOwner](https://github.com/scaffold-eth/se-2-challenges/assets/55535804/e8397b1e-a077-4009-b518-30a6d8deb6e7)

> ⚠️ But wait, I am not the owner! You will want to set your front end address as the owner in `01_deploy_riggedRoll.ts`. This will allow your front end address to call the withdraw function.

<details markdown='1'>
<summary>🔎 Hint</summary>

- You should be able to withdraw the full contract balance.
- Use `call` to transfer ETH.
- You should revert with `InsufficientBalance(requested, available)` if `_amount` is greater than `address(this).balance`.

<details markdown='1'>
<summary>🎯 Solution</summary>

```solidity
function withdraw(address _addr, uint256 _amount) external onlyOwner {
    uint256 available = address(this).balance;
    if (_amount > available) revert InsufficientBalance(_amount, available);
    (bool success, ) = payable(_addr).call{value: _amount}("");
    require(success, "Withdraw failed");
}
```

</details>
</details>

### 🥅 Goals

- [ ] Can you send value from the RiggedRoll contract to your front end address?
- [ ] Is anyone able to call the withdraw function or only the owner?

### Testing your progress

🔍 Run the following command to check if you implemented the withdraw function correctly:

```shell
yarn test --grep "Checkpoint3"
```

✅ Did the tests pass? You can dig into any errors by viewing the tests at `packages/hardhat/test/RiggedRoll.ts`.

## Checkpoint 4: 💾 Deploy your contracts! 🛰

📡 Edit the `defaultNetwork` in `hardhat.config.ts` to match the name of one of testnets from the `networks` object. We recommend to use `"sepolia"` or `"optimismSepolia"`

🔐 You will need to generate a **deployer address** using `yarn generate` This creates a mnemonic and saves it locally.

👩‍🚀 Use `yarn account` to view your deployer account balances.

⛽️ You will need to send ETH to your deployer address with your wallet, or get it from a public faucet of your chosen network. You can also request ETH by sending a message with your new deployer address and preferred network in the [challenge Telegram](https://t.me/+3StA0aBSArFjNjUx). People are usually more than willing to share.

🚀 Run `yarn deploy` to deploy your smart contract to a public network (selected in `hardhat.config.ts`)

> 💬 Hint: Instead of editing `hardhat.config.ts` you can just add a network flag to the deploy command like this: `yarn deploy --network sepolia` or `yarn deploy --network optimismSepolia`

---

## Checkpoint 5: 🚢 Ship your frontend! 🚁

✏️ Edit your frontend config in `packages/nextjs/scaffold.config.ts` to change the `targetNetwork` to `chains.sepolia` (or `chains.optimismSepolia` if you deployed to OP Sepolia)

💻 View your frontend at http://localhost:3000 and verify you see the correct network.

📡 When you are ready to ship the frontend app...

📦 Run `yarn vercel` to package up your frontend and deploy.

> You might need to log in to Vercel first by running `yarn vercel:login`. Once you log in (email, GitHub, etc), the default options should work.

> If you want to redeploy to the same production URL you can run `yarn vercel --prod`. If you omit the `--prod` flag it will deploy it to a preview/test URL.

> Follow the steps to deploy to Vercel. It'll give you a public URL.

> 🦊 Since we have deployed to a public testnet, you will now need to connect using a wallet you own or use a burner wallet. By default 🔥 `burner wallets` are only available on `hardhat` . You can enable them on every chain by setting `onlyLocalBurnerWallet: false` in your frontend config (`scaffold.config.ts` in `packages/nextjs/`)

#### Configuration of Third-Party Services for Production-Grade Apps.

By default, 🏗 Scaffold-ETH 2 provides predefined API keys for popular services such as Alchemy and Etherscan. This allows you to begin developing and testing your applications more easily, avoiding the need to register for these services.
This is great to complete your **SpeedRunEthereum**.

For production-grade applications, it's recommended to obtain your own API keys (to prevent rate limiting issues). You can configure these at:

- 🔷`ALCHEMY_API_KEY` variable in `packages/hardhat/.env` and `packages/nextjs/.env.local`. You can create API keys from the [Alchemy dashboard](https://dashboard.alchemy.com/).

- 📃`ETHERSCAN_API_KEY` variable in `packages/hardhat/.env` with your generated API key. You can get your key [here](https://etherscan.io/myapikey).

> 💬 Hint: It's recommended to store env's for nextjs in Vercel/system env config for live apps and use .env.local for local testing.

---

## Checkpoint 6: 📜 Contract Verification

Run the `yarn verify --network your_network` command to verify your contracts on etherscan 🛰

👉 Search this address on [Sepolia Etherscan](https://sepolia.etherscan.io/) (or [Optimism Sepolia Etherscan](https://sepolia-optimism.etherscan.io/) if you deployed to OP Sepolia) to get the URL you submit to 🏃‍♀️[SpeedRunEthereum.com](https://speedrunethereum.com).

---

> 🏃 Head to your next challenge [here](https://speedrunethereum.com).

> 💬 Problems, questions, comments on the stack? Post them to the [🏗 scaffold-eth developers chat](https://t.me/joinchat/F7nCRK3kI93PoCOk)

## Documentation

Visit our [docs](https://docs.scaffoldeth.io) to learn how to start building with Scaffold-ETH 2.

To know more about its features, check out our [website](https://scaffoldeth.io).

## Contributing to Scaffold-ETH 2

We welcome contributions to Scaffold-ETH 2!

Please see [CONTRIBUTING.MD](https://github.com/scaffold-eth/scaffold-eth-2/blob/main/CONTRIBUTING.md) for more information and guidelines for contributing to Scaffold-ETH 2.