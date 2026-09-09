"""AI drafts only; no provider is given a mutation tool or a credential."""
import json
import os
import re
from urllib.parse import urlparse
import httpx

def draft(prompt):
    provider = os.getenv("AI_PROVIDER", "demo")
    if provider == "demo":
        text = prompt.lower().strip()
        role = "viewer"
        if re.search(r'\b(suspend|disable)\b', text): action = "suspend"
        elif re.search(r'\b(restore|enable|reactivate)\b', text): action = "restore"
        elif re.search(r'\b(viewer|operator|admin)\b', text):
            action = "change_role"
            role = re.search(r'\b(viewer|operator|admin)\b', text).group()
        else: raise ValueError("Try: suspend access, restore access, or change role to viewer/operator/admin")
        return {"action": action, "role": role,
                "reason": "Deterministic demo interpretation. Review the selected identity and requested change.",
                "provider": "demo (rules, no model)"}
    if provider != "azure": raise ValueError("Unknown AI_PROVIDER")
    endpoint = os.getenv("AZURE_OPENAI_ENDPOINT", "").rstrip("/")
    parsed = urlparse(endpoint)
    if parsed.scheme != "https" or not parsed.hostname or parsed.username or parsed.query or parsed.path not in ("", "/"):
        raise ValueError("Configure an HTTPS Azure OpenAI resource endpoint")
    key = os.getenv("AZURE_OPENAI_API_KEY", "")
    model = os.getenv("AZURE_OPENAI_DEPLOYMENT", "")
    if not key or not model: raise ValueError("Azure AI credentials or deployment are missing")
    response = httpx.post(endpoint + "/openai/v1/chat/completions", timeout=20,
        headers={"api-key": key}, json={"model": model,
        "messages": [{"role": "system", "content":
            'Interpret the request as ONE access change. Return JSON with action (suspend, restore, change_role), '
            'role (viewer, operator, admin; viewer for non-role actions), and reason (brief rationale). '
            'Do not invent facts, execute actions or include personal data. '
            'If ambiguous, return {"error":"Please specify one access change"}.'},
            {"role": "user", "content": prompt}], "response_format": {"type": "json_object"}})
    response.raise_for_status()
    data = json.loads(response.json()["choices"][0]["message"]["content"])
    if (not isinstance(data, dict) or data.get("action") not in ("suspend", "restore", "change_role")
            or data.get("role") not in ("viewer", "operator", "admin")
            or not isinstance(data.get("reason"), str) or not 1 <= len(data["reason"]) <= 600):
        raise ValueError("AI output was ambiguous or invalid; specify one access change")
    return {"action": data["action"], "role": data["role"], "reason": data["reason"], "provider": "azure"}
