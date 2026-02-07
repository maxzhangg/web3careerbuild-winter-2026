export const contractAbi = [
  {
    type: "constructor",
    inputs: [{ name: "initialMessage", type: "string", internalType: "string" }],
    stateMutability: "nonpayable"
  },
  {
    type: "event",
    name: "MessageUpdated",
    inputs: [
      { name: "newMessage", type: "string", indexed: false, internalType: "string" },
      { name: "updatedBy", type: "address", indexed: true, internalType: "address" }
    ],
    anonymous: false
  },
  {
    type: "function",
    name: "getMessage",
    inputs: [],
    outputs: [{ name: "", type: "string", internalType: "string" }],
    stateMutability: "view"
  },
  {
    type: "function",
    name: "owner",
    inputs: [],
    outputs: [{ name: "", type: "address", internalType: "address" }],
    stateMutability: "view"
  },
  {
    type: "function",
    name: "setMessage",
    inputs: [{ name: "newMessage", type: "string", internalType: "string" }],
    outputs: [],
    stateMutability: "nonpayable"
  }
] as const;

export const contractAddress = process.env.NEXT_PUBLIC_CONTRACT_ADDRESS as `0x${string}`;
export const sepoliaRpcUrl = process.env.NEXT_PUBLIC_SEPOLIA_RPC_URL as string;
