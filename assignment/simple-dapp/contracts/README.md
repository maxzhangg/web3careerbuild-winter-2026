# Contracts

## 1) Install

```bash
npm install
```

## 2) Configure env

```bash
cp .env.example .env
```

Fill:
- `SEPOLIA_RPC_URL`
- `PRIVATE_KEY` (without `0x`)
- `ETHERSCAN_API_KEY` (optional, for verification)

## 3) Compile and test

```bash
npm run compile
npm run test
```

## 4) Deploy to Sepolia

```bash
npm run deploy:sepolia
```

Copy deployed address for frontend.
