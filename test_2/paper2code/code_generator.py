import json

try:
    from .llm_client import LLMClient
    from .prompts import CODE_GEN_SYSTEM, CODE_GEN_USER
    from .config import PipelineConfig
except ImportError:
    from llm_client import LLMClient
    from prompts import CODE_GEN_SYSTEM, CODE_GEN_USER
    from config import PipelineConfig


class CodeGenerator:
    def __init__(self, llm_client: LLMClient, config: PipelineConfig):
        self.llm = llm_client
        self.config = config

    def generate(self, analysis: dict) -> str:
        user_prompt = CODE_GEN_USER.format(
            problem=analysis.get("problem", ""),
            method_steps_json=json.dumps(
                analysis.get("method_steps", []), ensure_ascii=False, indent=2
            ),
            dataset=analysis.get("dataset", ""),
            metrics=analysis.get("metrics", ""),
        )
        raw = self.llm.chat(CODE_GEN_SYSTEM, user_prompt)
        return self._extract_code(raw)

    def _extract_code(self, raw: str) -> str:
        text = raw.strip()
        if "```python" in text:
            start = text.find("```python") + len("```python")
            end = text.find("```", start)
            if end != -1:
                return text[start:end].strip()
        elif "```" in text:
            start = text.find("```") + 3
            end = text.find("```", start)
            if end != -1:
                return text[start:end].strip()
        return text
