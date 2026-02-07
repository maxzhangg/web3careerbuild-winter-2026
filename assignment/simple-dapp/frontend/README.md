# Frontend

## 1) Install

```bash
npm install
```

## 2) Configure env

```bash
cp .env.example .env.local
```

Set:
- `NEXT_PUBLIC_CONTRACT_ADDRESS` from deployment output
- `NEXT_PUBLIC_SEPOLIA_RPC_URL`

## 3) Run locally

```bash
npm run dev
```

Open `http://localhost:3000`.

## 4) Deploy to Vercel

Push this folder to your git repo and import into Vercel (or set root directory to `simple-dapp/frontend`).
