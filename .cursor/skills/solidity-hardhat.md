---
name: solidity-hardhat
description: Solidity & Hardhat Technical Encyclopedia: Ethers.js v6, Waffle/Chai Testing, Hardhat Ignition, and Fork Orchestration.
---

# Skill: Solidity & Hardhat (Technical Encyclopedia)

[Back to README](../../README.md)

Comprehensive technical protocols for the development and testing of Ethereum Smart Contracts using the Solidity language and the Hardhat/Typescript toolchain in the 2025 ecosystem. This document defines the standards for Ethers.js v6 integration, Waffle/Chai-based testing, and automated multi-chain deployment via Hardhat Ignition.

---

## 1. The Hardhat / TS Stack Standards
Standardizing on TypeScript for robust, type-safe smart contract interaction.

### 1.1 Ethers.js v6 Integration Protocols
*   **Provider Management:** Utilizing the `JsonRpcProvider` for optimized interaction with RPC nodes.
*   **Contract Typing (TypeChain):** Mandatory use of TypeChain to generate TypeScript interfaces for all smart contracts, ensuring compile-time safety for function calls and events.

### 1.2 Implementation Protocol (Hardhat Test)
```typescript
import { expect } from "chai";
import { ethers } from "hardhat";

# 1.2.1 Fixture-Based Testing Standard
# Utilizing 'loadFixture' from @nomicfoundation/hardhat-network-helpers to ensure clean state.
async function deployContractFixture() {
    const [owner, otherAccount] = await ethers.getSigners();
    const Token = await ethers.getContractFactory("MyToken");
    const token = await Token.deploy();
    return { token, owner, otherAccount };
}
```

---

## 2. Testing Frameworks (Waffle & Chai)
Leveraging the JS ecosystem for complex, behavioral-driven smart contract testing.

### 2.1 Expectation Standards
*   **Event Emitting:** `await expect(tx).to.emit(contract, "Transfer").withArgs(...)`.
*   **Reversion Checks:** `await expect(tx).to.be.revertedWith("Insufficient Balance")`.
*   **Balance Changes:** Utilizing `changeEtherBalance` and `changeTokenBalance` for high-resolution checking of accounting logic.

---

## 3. Deployment & Orchestration (Hardhat Ignition)
The 2025 standard for declarative, resumable deployments.

### 3.1 Module-Based Deployment
*   **Logic:** Defining deployment "Modules" that describe the desired state of the system, allowing Hardhat Ignition to handle cross-contract dependencies and automated retries.
*   **Verification:** Automatic Etherscan/Polygonscan verification integrated into the deployment process.

---

## 4. Technical Appendix: Hardhat Reference
| Plugin | Technical Purpose | Standard |
| :--- | :--- | :--- |
| **@nomicfoundation/hardhat-toolbox**| Consolidated toolchain | Mandatory |
| **hardhat-gas-reporter** | Real-time gas cost auditing | P0 (Critical) |
| **solidity-coverage** | Line/Branch coverage metrics | Target 95% |
| **hardhat-network** | Local Ethereum fork | Local Testing |

---

## 5. Industrial Case Study: Upgrading a Live NFT Project
**Objective:** Adding "Staking" capabilities to an existing ERC-721 collection.
1.  **Forking:** Creating a local fork of the Mainnet at a specific block height.
2.  **Impersonating:** Using `getSigner` as the collection owner to test admin-only functions.
3.  **Deployment:** Using Hardhat Ignition to deploy the new Staking contract and link it to the existing collection.
4.  **Verification:** Running the full test suite against the live Mainnet state to ensure no "State Collision" occurs.

---

## 6. Glossary of Hardhat terms
*   **Task:** A custom script that can be executed from the Hardhat CLI.
*   **Fixture:** A function that sets up the environment for a test run.
*   **Signer:** An abstraction of an Ethereum Account, which can be used to sign messages and transactions.
*   **Provider:** An abstraction of a connection to the Ethereum Network.

---

## 7. Mathematical Foundations: Gas Price Estimation
*   **Logic:** Calculating `maxPriorityFeePerGas` and `maxFeePerGas` (EIP-1559 standard) to ensure transactions are included in the next block without overpaying.
*   **Optimization:** In 2025, Hardhat scripts utilize history-based gas price oracles to optimize deployment costs.

---

## 8. Troubleshooting & Performance Verification
*   **Mismatched Compilers:** Different contracts in the same project requiring different Solidity versions. *Fix: Use the `compilers` array in `hardhat.config.ts`.*
*   **Network Timeouts:** RPC nodes failing during long test runs. *Fix: Implement "Retry" logic in the provider and increase global timeouts.*

---

## 9. Appendix: Future "Hardhat" Extensions
*   **Shadow Prototyping:** Utilizing Hardhat to simulate complex DeFi interactions (e.g., Flashloans) without writing a single line of production code.

---

## 10. Benchmarks & Performance Standards (2025)
*   **Test Execution Time:** Target < 2s for unit tests; < 10s for integration tests with local forking.
*   **Deployment Reliability:** 100% success rate for multi-chain rollouts using Hardhat Ignition.

---
[Back to README](../../README.md)
