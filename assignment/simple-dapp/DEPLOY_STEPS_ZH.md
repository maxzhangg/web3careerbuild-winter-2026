# 手动部署步骤（Sepolia + Vercel）

以下命令均在 `simple-dapp` 目录下执行。

## 0. 前置准备

1. 安装 Node.js 18+（建议 Node.js 20 LTS）
2. 准备 Sepolia RPC（Infura/Alchemy 任意）
3. 钱包准备少量 Sepolia ETH（用于部署和写入）
4. 准备 Vercel 账号并绑定你的 Git 仓库

## 1. 部署智能合约到 Sepolia

进入合约目录：

```bash
cd contracts
```

安装依赖：

```bash
npm install
```

配置环境变量：

```bash
cp .env.example .env
```

编辑 `.env`：
- `SEPOLIA_RPC_URL`
- `PRIVATE_KEY`（不要带 `0x`）
- `ETHERSCAN_API_KEY`（可选）

编译和测试：

```bash
npm run compile
npm run test
```

部署到 Sepolia：

```bash
npm run deploy:sepolia
```

记下终端输出的合约地址（`SimpleStorage deployed to: 0x...`）。

## 2. 本地启动前端并连接合约

进入前端目录：

```bash
cd ../frontend
```

安装依赖：

```bash
npm install
```

配置前端环境变量：

```bash
cp .env.example .env.local
```

编辑 `.env.local`：
- `NEXT_PUBLIC_CONTRACT_ADDRESS=你的合约地址`
- `NEXT_PUBLIC_SEPOLIA_RPC_URL=你的 Sepolia RPC`

本地启动：

```bash
npm run dev
```

浏览器打开 `http://localhost:3000`，MetaMask 切到 Sepolia 测试：
1. `Connect Wallet`
2. 输入新消息
3. `Set Message`

## 3. 部署前端到 Vercel

1. 把 `simple-dapp` 提交并推送到远程仓库
2. Vercel 新建项目，选择该仓库
3. Root Directory 设为 `simple-dapp/frontend`
4. 在 Vercel 项目环境变量添加：
   - `NEXT_PUBLIC_CONTRACT_ADDRESS`
   - `NEXT_PUBLIC_SEPOLIA_RPC_URL`
5. 点击 Deploy

部署完成后，打开 Vercel 域名即可访问 DApp。
