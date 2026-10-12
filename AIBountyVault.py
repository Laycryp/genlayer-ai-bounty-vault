# v0.2.16
# { "Depends": "py-genlayer:1jb45aa8ynh2a9c9xn3b7qqh8sm5q93hwfp7jqmwsfhh8jpz09h6" }

from genlayer import *
import json

class AIBountyVault(gl.Contract):
    protocol_name: str
    protocol_repo_url: str
    bounties_json: str  # تخزين القاموس كـ JSON لإدارة عدة ثغرات في عقد واحد
    total_paid_out: u256
    admin: str  # تمرير عنوان المدير كمعلمة لتجنب خطأ __init__

    def __init__(self, protocol_name: str, protocol_repo_url: str, admin_address: str):
        self.protocol_name = protocol_name
        self.protocol_repo_url = protocol_repo_url
        self.bounties_json = "{}"
        self.total_paid_out = u256(0)
        self.admin = admin_address

    @gl.public.write
    def create_bounty(self, bug_id: str, description: str, reward_amount: int) -> str:
        caller = gl.message.sender
        if caller != self.admin:
            raise gl.vm.UserError("Only the admin can create bounties.")
            
        bounties = json.loads(self.bounties_json)
        if bug_id in bounties:
            raise gl.vm.UserError("Bounty ID already exists.")
            
        bounties[bug_id] = {
            "description": description,
            "reward": reward_amount,
            "solved_by": "",
            "is_open": True
        }
        self.bounties_json = json.dumps(bounties)
        return "Bounty " + bug_id + " created successfully."

    @gl.public.write
    def submit_patch(self, bug_id: str, patch_url: str) -> str:
        caller = gl.message.sender
        bounties = json.loads(self.bounties_json)
        
        if bug_id not in bounties:
            raise gl.vm.UserError("Bounty ID not found.")
            
        if not bounties[bug_id]["is_open"]:
            raise gl.vm.UserError("This bounty is already solved or closed.")

        desc = bounties[bug_id]["description"]

        def evaluate_patch() -> dict:
            try:
                patch_data = gl.nondet.web.render(patch_url, mode="text")
                if not patch_data or len(patch_data) < 10:
                    return {"is_valid": False, "error": True, "reason": "Failed to fetch patch data."}
            except Exception:
                return {"is_valid": False, "error": True, "reason": "Network fetch error."}

            # دمج النصوص العادي لتفادي ثغرة محرك GenVM مع النصوص المعقدة
            task = (
                "You are an expert Smart Contract Security Auditor AI.\n"
                "Vulnerability Description: " + desc + "\n"
                "Proposed Patch Data:\n" + str(patch_data[:2000]) + "\n\n"
                "Does this patch securely and fully fix the described vulnerability?\n"
                "Respond using ONLY this JSON format:\n"
                '{"is_valid": bool, "reason": "short technical explanation"}'
            )

            try:
                result_str = gl.nondet.exec_prompt(task).replace("```json", "").replace("```", "")
                parsed = json.loads(result_str)
                if "is_valid" not in parsed:
                    return {"is_valid": False, "error": True, "reason": "Invalid LLM JSON."}
                parsed["error"] = False
                return parsed
            except Exception:
                return {"is_valid": False, "error": True, "reason": "LLM parsing failed."}

        consensus = gl.eq_principle.strict_eq(evaluate_patch)

        if consensus.get("error"):
            raise gl.vm.UserError("Evaluation failed: " + str(consensus.get("reason")))

        if consensus["is_valid"]:
            bounties[bug_id]["is_open"] = False
            bounties[bug_id]["solved_by"] = caller
            reward = bounties[bug_id]["reward"]
            self.total_paid_out += u256(reward)
            self.bounties_json = json.dumps(bounties)
            return "SUCCESS: Patch accepted. Bounty " + bug_id + " awarded to " + caller

        return "FAILED: Patch rejected. Reason: " + str(consensus.get("reason"))

    @gl.public.view
    def get_bounty_status(self, bug_id: str) -> str:
        bounties = json.loads(self.bounties_json)
        if bug_id not in bounties:
            return "Bounty not found."
        return json.dumps(bounties[bug_id])