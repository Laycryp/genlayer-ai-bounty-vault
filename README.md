# AI Smart Contract Bug Bounty Vault

An autonomous, AI-driven bug bounty platform built on GenLayer.
This Intelligent Contract manages multiple bug bounties simultaneously, evaluating submitted security patches through non-deterministic LLM consensus before autonomously recording successful resolutions.

## Architectural Overview

This contract demonstrates advanced state management and strict adherence to GenVM security standards, solving real-world Web3 security coordination.

* **Complex State Management:** Bypasses basic flat storage limitations by utilizing serialized JSON dictionaries to manage an arbitrary number of concurrent bounties within a single state variable.
* **Zero-Trust Access Control:** Enforces strict role-based execution. Only the designated admin (set at initialization) can create bounties.
* **Deterministic Consensus on Non-Deterministic Data:** Evaluates external patch URLs by rendering Web2 data and running it through an LLM.
The state transition only occurs if validators achieve strict consensus (`gl.eq_principle.strict_eq`) on the validity of the patch.
* **GenVM Parsing Compliance:** Utilizes direct string concatenation for complex LLM prompts, completely avoiding GenVM's known parsing issues with multi-line f-strings and nested brackets.
* **Graceful Degradation:** Wraps all external web fetches and LLM JSON parsing in robust `try/except` blocks, ensuring the contract fails safely rather than bricking the state during timeouts.

## Contract Workflow

1. **Initialization:** The contract is deployed with the target protocol's details and the Admin's verified address.
2. **Bounty Creation:** The Admin invokes `create_bounty` with a unique ID, description, and reward. The state is updated via JSON serialization.
3. **Patch Submission:** A security researcher submits a URL containing their proposed fix via `submit_patch`.
4. **AI Consensus:** The GenVM network fetches the patch data, analyzes it against the vulnerability description using LLMs, and votes.
5. **Resolution:** If strict consensus determines the patch is valid, the bounty is permanently marked as closed and the solver's address is recorded on-chain.