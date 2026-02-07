# Simple DApp

A minimal full-stack DApp example that includes:
- Solidity + Hardhat smart contract development and Sepolia deployment
- Next.js + viem frontend interaction
- Vercel frontend hosting

## Online Demo

- Production URL: `https://simple-dapp-9yzwsly28-ms-projects-58b86da7.vercel.app`
- Network: `Ethereum Sepolia`
- Contract: `0xc635bf97c2dE521B6B9466615f069645b695752E`

## Features

- Read on-chain message via `getMessage()`
- Update on-chain message via `setMessage(string)`
- Connect wallet with MetaMask
- Listen to `MessageUpdated` event and refresh UI

## Tech Stack

- Smart Contract: `Solidity 0.8.24`
- Contract Tooling: `Hardhat`, `@nomicfoundation/hardhat-toolbox`
- Frontend: `Next.js 14`, `React 18`, `TypeScript`
- Web3 Client: `viem`
- Hosting: `Vercel`

## Project Structure

```text
simple-dapp/
  README.md
  DEPLOY_STEPS_ZH.md
  contracts/
    contracts/SimpleStorage.sol
    scripts/deploy.js
    hardhat.config.js
    .env.example
    README.md
  frontend/
    app/page.tsx
    lib/contract.ts
    .env.example
    vercel.json
    README.md
```

## Contract Overview

`SimpleStorage` provides:
- Constructor to initialize message
- `getMessage()` to read current message
- `setMessage(string)` to update message and emit `MessageUpdated`

Source: `simple-dapp/contracts/contracts/SimpleStorage.sol`

## Local Development

### 1) Deploy contract to Sepolia

```bash
cd simple-dapp/contracts
npm install
cp .env.example .env
```

Fill `simple-dapp/contracts/.env`:
- `SEPOLIA_RPC_URL`
- `PRIVATE_KEY` (without `0x`)
- `ETHERSCAN_API_KEY` (optional)

Run:

```bash
npm run compile
npm run test
npm run deploy:sepolia
```

### 2) Run frontend

```bash
cd ../frontend
npm install
cp .env.example .env.local
```

Fill `simple-dapp/frontend/.env.local`:
- `NEXT_PUBLIC_CONTRACT_ADDRESS=0xc635bf97c2dE521B6B9466615f069645b695752E`
- `NEXT_PUBLIC_SEPOLIA_RPC_URL=<your_sepolia_rpc_url>`

Start:

```bash
npm run dev
```

Open: `http://localhost:3000`

## Deploy to Vercel (CLI)

Run in `simple-dapp/frontend`:

```bash
vercel login
vercel link
vercel env add NEXT_PUBLIC_CONTRACT_ADDRESS production
vercel env add NEXT_PUBLIC_SEPOLIA_RPC_URL production
vercel --prod
```

Notes:
- `NEXT_PUBLIC_*` variables are public in browser bundles
- Redeploy after changing Vercel environment variables

## Troubleshooting

- `Missing env`
  - Check variable names in `frontend/.env.local`
  - Restart `npm run dev` after editing env
- `invalid project id`
  - RPC key in `SEPOLIA_RPC_URL` is invalid
- Vercel `No Output Directory named "public"`
  - Ensure `frontend/vercel.json` exists and sets `framework` to `nextjs`

## Security Notes

- Do not commit `contracts/.env`
- Use test wallet and test ETH on Sepolia only
- Never put private keys in frontend code or public env variables
