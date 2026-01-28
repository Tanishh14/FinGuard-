import os
import requests
from pathlib import Path

OLLAMA_URL = "http://localhost:11434/api/generate"
MODEL_NAME = "llama3.1:8b"

PROMPT_PATH = Path(__file__).parent / "prompt_templates" / "fraud_explain.txt"


class LLMExplainer:
    def __init__(self):
        self.prompt_template = PROMPT_PATH.read_text(encoding="utf-8")
        self.disable_llm = os.getenv("DISABLE_LLM", "false").lower() == "true"

    def explain(self, transaction: dict, model_signals: dict, retrieved_context: str) -> str:
        # 🔥 TEST / CI SAFE MODE
        if self.disable_llm:
            return (
                "Mock Explanation:\n"
                "- Multiple anomaly indicators detected\n"
                "- High behavioral deviation\n"
                "- Elevated fraud risk\n"
                "Confidence: High"
            )

        prompt = self.prompt_template.format(
            context=retrieved_context,
            transaction=transaction,
            signals=model_signals,
        )

        payload = {
            "model": MODEL_NAME,
            "prompt": prompt,
            "stream": False,
            "options": {"temperature": 0.2, "top_p": 0.9},
        }

        response = requests.post(OLLAMA_URL, json=payload, timeout=120)
        response.raise_for_status()

        return response.json()["response"].strip()
