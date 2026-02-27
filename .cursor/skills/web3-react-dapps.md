---
name: web3-react-dapps
description: Web3 React DApps Technical Encyclopedia: Wagmi v2, Viem Low-Level RPC, WalletConnect v2, and React Query State Management.
---

# Skill: Web3 React DApps (Technical Encyclopedia)

[Back to README](../../README.md)

Comprehensive technical protocols for the design and construction of decentralized applications (DApps) using React and the modern Web3 stack in the 2025 ecosystem. This document defines the standards for Wagmi v2 orchestration, Viem-based RPC communication, and high-performance blockchain state management.

---

## 1. Web3 Frontend Architectures (Wagmi & Viem)
Standardizing on the most performant and type-safe stack for React-based DApps.

### 1.1 Wagmi v2 Orchestration Standard
*   **Logic:** Utilizing the `WagmiConfig` to provide a global context for wallet connection, contract interaction, and network switching.
*   **Viem Interop:** Leveraging Viem as the underlying lightweight, type-safe library for encoding and decoding ABI data.
*   **Hook Patterns:** Mandatory use of specialized hooks (e.g., `useAccount`, `useConnect`, `useContractRead`) for reactive UI updates.

### 1.2 Implementation Protocol (Wagmi Setup)
```typescript
import { createConfig, http } from 'wagmi'
import { mainnet, polygon } from 'wagmi/chains'

# 1.2.1 Mandatory Chain Configuration
export const config = createConfig({
  chains: [mainnet, polygon],
  transports: {
    [mainnet.id]: http(),
    [polygon.id]: http(),
  },
})
```

---

## 2. Advanced Wallet Integration (WalletConnect v2)
Standardizing on the industry-leading protocol for mobile and desktop wallet connectivity.

### 2.1 WalletConnect v2 Standards
*   **Pairing & Sessions:** Implementing robust session management to handle multi-chain connections and persistent pairings across page reloads.
*   **Sign-In With Ethereum (SIWE):** Utilizing the EIP-4361 standard for secure, message-based authentication without relying on centralized passwords.

---

## 3. Blockchain State Management (React Query)
Managing the high-latency, volatile state of the blockchain.

### 3.1 Caching & Revalidation Protocols
*   **Logic:** Utilizing React Query (integrated into Wagmi) to cache contract data and automatically revalidate on new block events.
*   **Background Fetching:** Ensuring that the UI remains responsive by fetching data in the background and only showing "Loading" states for critical, un-cached data.

### 3.2 Error & Rejection Handling
*   **Protocol:** Mandatory standard for handling user-rejected transactions (Code 4001) and internal RPC errors without crashing the application.

---

## 4. Technical Appendix: Web3 DApp Reference
| Hook / Tool | Technical Purpose | Standard |
| :--- | :--- | :--- |
| `useReadContract` | Fetching data from the chain | Reactive |
| `useWriteContract` | Sending transactions | User-triggered |
| `useWaitForTransactionReceipt` | Monitoring tx status | Essential |
| `ConnectKit` / `RainbowKit` | UI for wallet selection | Recommended |

---

## 5. Industrial Case Study: Multi-Chain NFT Marketplace
**Objective:** Building a fast, secure marketplace for Ethereum and Polygon.
1.  **Architecture:** Utilizing Wagmi v2 for multi-chain configuration.
2.  **Indexing:** Using Subgraph (The Graph) or Reservoir for real-time asset indexing.
3.  **Transaction Handling:** Implementing a "Transaction Queue" UI that shows the status of multiple concurrent mint/buy/sell actions.
4.  **Verification:** Utilizing SIWE to allow users to set up a profile that persists across different wallets.

---

## 6. Glossary of Web3 DApp Terms
*   **ABI (Application Binary Interface):** The technical specification for interacting with a smart contract.
*   **RPC (Remote Procedure Call):** The protocol used to communicate with a blockchain node.
*   **Gas:** The cost of executing a transaction on the network.
*   **Nonce:** A number that ensures a transaction is only processed once.
*   **EIP (Ethereum Improvement Proposal):** A technical standard for the Ethereum network.

---

## 7. Mathematical Foundations: Gas Estimation in React
*   **Logic:** Predicting the cost of a transaction before it is sent to ensure the user has sufficient funds.
*   **Formula:** $\text{Total Cost} = \text{GasLimit} \cdot \text{BaseFee} + \text{PriorityFee}$.
*   **Optimization:** In 2025, DApps calculate a 20% "Safety Buffer" on the GasLimit to prevent out-of-gas failures during volatile network periods.

---

## 8. Troubleshooting & Performance Verification
*   **Chain ID Mismatch:** User's wallet is on the wrong network. *Fix: Use automated `switchChain` prompts.*
*   **Old Cached Data:** Showing an incorrect balance. *Fix: Trigger an invalidate on every block event via `useBlockNumber`.*
*   **Missing Providers:** Injected wallets (MetaMask) failing to load. *Fix: Implement robust "Provider Detection" logic.*

---

## 9. Appendix: Future "ZK" Extensions
*   **Zero-Knowledge Proofs (ZKP):** Integrating ZK-friendly libraries (e.g., Circom, SnarkJS) to allow users to prove facts (e.g., "I own this NFT") without revealing their identity or full wallet history.

---

## 10. Benchmarks & Performance Standards (2025)
*   **Connection Speed:** Target < 2s for initial wallet pairing.
*   **UI Reactivity:** 100% agreement between the visible UI state and the latest blockchain block number.

---
[Back to README](../../README.md)
