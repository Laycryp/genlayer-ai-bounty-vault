# v0.2.16
# { "Depends": "py-genlayer:1jb45aa8ynh2a9c9xn3b7qqh8sm5q93hwfp7jqmwsfhh8jpz09h6" }

from genlayer import *
import json

class AIBountyVault(gl.Contract):
    protocol_name: str
    protocol_repo_url: str
    bounties_json: str
    total_paid_out: u256
    admin: str

    def __init__(self, protocol_name: str, protocol_repo_url: str, admin_address: str):
        self.protocol_name = protocol_name
        self.protocol_repo_url = protocol_repo_url.rstrip("/")
        self.bounties_json = "{}"
        self.total_paid_out = u256(0)
        self.admin = admin_address

    @gl.public.write
    def create_bounty(
        self,
        bug_id: str,
        description: str,
        vulnerable_file_path: str,
        source_version: str,
        reward_amount: int
    ) -> str:
        caller = gl.message.sender
        if caller != self.admin:
            raise gl.vm.UserError("Only the admin can create bounties.")

        if reward_amount <= 0:
            raise gl.vm.UserError("Reward amount must be positive.")

        bounties = json.loads(self.bounties_json)
        if bug_id in bounties:
            raise gl.vm.UserError("Bounty ID already exists.")

        clean_path = vulnerable_file_path.lstrip("/")
        # ربط مستودع البروتوكول مع الإصدار والملف المصاب لتكوين رابط المصدر الفعلي
        source_url = self.protocol_repo_url + "/" + source_version + "/" + clean_path

        bounties[bug_id] = {
            "description": description,
            "vulnerable_file_path": clean_path,
            "source_version": source_version,
            "source_url": source_url,
            "reward": reward_amount,
            "solved_by": "",
            "accepted_patch_url": "",
            "is_open": True
        }
        self.bounties_json = json.dumps(bounties)
        return "Bounty " + bug_id + " created for source: " + source_url

    @gl.public.write
    def submit_patch(self, bug_id: str, patch_url: str) -> str:
        caller = gl.message.sender
        bounties = json.loads(self.bounties_json)

        if bug_id not in bounties:
            raise gl.vm.UserError("Bounty ID not found.")

        bounty = bounties[bug_id]
        if not bounty["is_open"]:
            raise gl.vm.UserError("This bounty is already solved or closed.")

        desc = bounty["description"]
        source_url = bounty["source_url"]
        source_version = bounty["source_version"]
        file_path = bounty["vulnerable_file_path"]
        repo_url = self.protocol_repo_url

        def evaluate_patch() -> dict:
            # 1. جلب الكود الأصلي المصاب بالكامل من مستودع البروتوكول
            try:
                vulnerable_source = gl.nondet.web.render(source_url, mode="text")
                if not vulnerable_source or len(vulnerable_source.strip()) == 0:
                    return {"is_valid": False, "error": True, "reason": "Failed to fetch vulnerable source from protocol repository."}
            except Exception:
                return {"is_valid": False, "error": True, "reason": "Network error fetching vulnerable source code."}

            # 2. جلب الرقعة البرمجية الكاملة بدون أي اقتطاع (No truncation)
            try:
                patch_data = gl.nondet.web.render(patch_url, mode="text")
                if not patch_data or len(patch_data.strip()) == 0:
                    return {"is_valid": False, "error": True, "reason": "Failed to fetch complete patch data."}
            except Exception:
                return {"is_valid": False, "error": True, "reason": "Network error fetching submitted patch."}

            # 3. تقييم الكود الأصلي والإصدار جنباً إلى جنب مع الرقعة الكاملة
            task = (
                "You are an expert Smart Contract Security Auditor AI.\n"
                "Protocol Repository: " + repo_url + "\n"
                "Target Version / Commit: " + source_version + "\n"
                "Affected File Path: " + file_path + "\n"
                "Vulnerability Description: " + desc + "\n\n"
                "--- ORIGINAL VULNERABLE SOURCE CODE ---\n"
                + str(vulnerable_source) + "\n\n"
                "--- COMPLETE PROPOSED PATCH ---\n"
                + str(patch_data) + "\n\n"
                "Evaluate the complete patch against the original vulnerable source code and version:\n"
                "1. Does the original source code from the repository contain the described vulnerability?\n"
                "2. Is the proposed patch compatible with this exact source version?\n"
                "3. Does the complete patch securely and fully fix the vulnerability without introducing regressions?\n"
                "Respond using ONLY this JSON format:\n"
                '{"is_valid": bool, "reason": "short technical explanation"}'
            )

            try:
                result_str = gl.nondet.exec_prompt(task).replace("```json", "").replace("```", "").strip()
                parsed = json.loads(result_str)
                if "is_valid" not in parsed or not isinstance(parsed["is_valid"], bool):
                    return {"is_valid": False, "error": True, "reason": "Invalid LLM JSON schema."}
                parsed["error"] = False
                return parsed
            except Exception:
                return {"is_valid": False, "error": True, "reason": "LLM execution or JSON parsing failed."}

        consensus = gl.eq_principle.strict_eq(evaluate_patch)

        if consensus.get("error"):
            raise gl.vm.UserError("Evaluation failed: " + str(consensus.get("reason")))

        if consensus["is_valid"]:
            bounty["is_open"] = False
            bounty["solved_by"] = caller
            bounty["accepted_patch_url"] = patch_url
            reward = bounty["reward"]
            self.total_paid_out += u256(reward)
            bounties[bug_id] = bounty
            self.bounties_json = json.dumps(bounties)
            return "SUCCESS: Complete patch verified against source version " + source_version + ". Bounty " + bug_id + " awarded to " + caller

        return "FAILED: Patch rejected. Reason: " + str(consensus.get("reason"))

    @gl.public.view
    def get_bounty_status(self, bug_id: str) -> str:
        bounties = json.loads(self.bounties_json)
        if bug_id not in bounties:
            return "Bounty not found."
        return json.dumps(bounties[bug_id])