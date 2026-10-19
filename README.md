# AI Smart Contract Bug Bounty Vault

An autonomous, AI-driven bug bounty platform built on GenLayer. This Intelligent Contract manages multiple concurrent bug bounties, verifying submitted security patches by fetching and cross-evaluating the original versioned source code from the protocol repository alongside the complete proposed patch through validator consensus.

## Architectural Overview

This contract implements end-to-end evidence verification and adheres strictly to GenVM security and storage constraints:

* **Versioned Source Context Acquisition:** Rather than relying solely on text descriptions, each bounty binds a specific `source_version` (branch or commit hash) and `vulnerable_file_path` to the configured `protocol_repo_url`.
* **Dual-Fetch Consensus Verification:** Inside the non-deterministic consensus block (`gl.eq_principle.strict_eq`), validators independently fetch both the original vulnerable source file from the protocol repository and the complete submitted patch without character truncation.
* **Complex State Management:** Utilizes serialized JSON dictionaries to manage multiple independent bounties, tracking target versions, affected file paths, accepted patch URLs, and solver identities within a single contract instance.
* **Strict Type and Syntax Compliance:** Uses `u256` for reward accounting and direct string concatenation for prompt construction to maintain full compatibility with the GenVM compiler.
* **Zero-Trust Access Control:** Enforces administrative permissions and solver attribution exclusively through `gl.message.sender`.
* **Fault-Tolerant Execution:** Wraps both external web renders and LLM JSON parsing in isolated `try/except` blocks to guarantee safe failure handling.

## Contract Workflow

1. **Initialization:** Deployed with the target protocol name, base raw repository URL (`protocol_repo_url`), and the administrator's address.
2. **Bounty Registration:** The administrator calls `create_bounty` with a unique identifier, vulnerability description, affected file path, target source version, and reward amount.
3. **Patch Evaluation:** A researcher calls `submit_patch` with the bounty identifier and a link to the complete patch.
4. **Validator Consensus:** Validators retrieve the original vulnerable source code and the full patch, verifying that the vulnerability exists in the specified version and that the patch resolves it completely without regressions.
5. **Resolution:** Upon achieving strict consensus, the contract locks the bounty, records the caller's address and accepted patch URL, and increments the total payout counter.