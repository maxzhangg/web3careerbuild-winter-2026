"use client";

import { useEffect, useMemo, useState } from "react";
import {
  createPublicClient,
  createWalletClient,
  custom,
  http,
  parseAbiItem
} from "viem";
import { sepolia } from "viem/chains";
import { contractAbi, contractAddress, sepoliaRpcUrl } from "../lib/contract";

const messageUpdatedEvent = parseAbiItem(
  "event MessageUpdated(string newMessage, address indexed updatedBy)"
);

export default function HomePage() {
  const [account, setAccount] = useState<string>("");
  const [currentMessage, setCurrentMessage] = useState<string>("");
  const [newMessage, setNewMessage] = useState<string>("");
  const [status, setStatus] = useState<string>("Disconnected");
  const [busy, setBusy] = useState<boolean>(false);

  const isConfigured = useMemo(() => {
    return Boolean(contractAddress && sepoliaRpcUrl);
  }, []);

  const publicClient = useMemo(() => {
    if (!isConfigured) return null;
    return createPublicClient({
      chain: sepolia,
      transport: http(sepoliaRpcUrl)
    });
  }, [isConfigured]);

  async function loadMessage() {
    if (!publicClient || !contractAddress) return;
    const message = (await publicClient.readContract({
      address: contractAddress,
      abi: contractAbi,
      functionName: "getMessage"
    })) as string;
    setCurrentMessage(message);
  }

  async function connectWallet() {
    try {
      if (!window.ethereum) {
        setStatus("MetaMask not found");
        return;
      }

      setStatus("Connecting wallet...");
      const chainIdHex = (await window.ethereum.request({
        method: "eth_chainId"
      })) as string;

      if (chainIdHex !== "0xaa36a7") {
        await window.ethereum.request({
          method: "wallet_switchEthereumChain",
          params: [{ chainId: "0xaa36a7" }]
        });
      }

      const accounts = (await window.ethereum.request({
        method: "eth_requestAccounts"
      })) as string[];

      if (!accounts.length) {
        setStatus("No wallet account");
        return;
      }

      setAccount(accounts[0]);
      setStatus("Wallet connected");
    } catch (error) {
      const message = error instanceof Error ? error.message : String(error);
      setStatus(`Connect failed: ${message.slice(0, 120)}`);
    }
  }

  async function submitMessage() {
    if (!window.ethereum) {
      setStatus("MetaMask not found");
      return;
    }
    if (!account) {
      setStatus("Connect wallet first");
      return;
    }
    if (!newMessage.trim()) {
      setStatus("Message cannot be empty");
      return;
    }
    if (!publicClient || !contractAddress) {
      setStatus("Missing frontend env config");
      return;
    }
    const walletClient = createWalletClient({
      chain: sepolia,
      transport: custom(window.ethereum)
    });
    setBusy(true);
    setStatus("Sending transaction...");
    try {
      const hash = await walletClient.writeContract({
        account: account as `0x${string}`,
        address: contractAddress,
        abi: contractAbi,
        functionName: "setMessage",
        args: [newMessage]
      });
      setStatus(`Tx sent: ${hash.slice(0, 10)}... waiting confirmation`);
      await publicClient.waitForTransactionReceipt({ hash });
      await loadMessage();
      setNewMessage("");
      setStatus("Message updated on chain");
    } catch (error) {
      const message = error instanceof Error ? error.message : String(error);
      setStatus(`Tx failed: ${message.slice(0, 120)}`);
    } finally {
      setBusy(false);
    }
  }

  useEffect(() => {
    loadMessage().catch(() => undefined);
    if (!publicClient || !contractAddress) return;

    const unwatch = publicClient.watchEvent({
      address: contractAddress,
      event: messageUpdatedEvent,
      onLogs: () => {
        loadMessage().catch(() => undefined);
      }
    });
    return () => unwatch();
  }, [publicClient]);

  return (
    <main>
      <section className="card">
        <h1>Simple Sepolia DApp</h1>
        <p>Read and update one on-chain message.</p>

        {!isConfigured ? (
          <p className="status">
            Missing env. Set `NEXT_PUBLIC_CONTRACT_ADDRESS` and
            `NEXT_PUBLIC_SEPOLIA_RPC_URL`.
          </p>
        ) : (
          <>
            <div className="row">
              <button onClick={connectWallet}>Connect Wallet</button>
              <button onClick={loadMessage}>Refresh Message</button>
            </div>

            <p className="mono">
              Wallet: {account ? account : "Not connected"}
            </p>
            <p>
              Current message: <strong>{currentMessage || "(empty)"}</strong>
            </p>

            <input
              type="text"
              placeholder="Enter new message"
              value={newMessage}
              onChange={(e) => setNewMessage(e.target.value)}
            />
            <button onClick={submitMessage} disabled={busy}>
              {busy ? "Pending..." : "Set Message"}
            </button>

            <p className="status">{status}</p>
          </>
        )}
      </section>
    </main>
  );
}
