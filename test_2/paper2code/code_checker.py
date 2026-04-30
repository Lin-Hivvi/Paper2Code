import json

try:
    from .llm_client import LLMClient
    from .pdf_parser import extract_text
    from .prompts import CHECK_SYSTEM, CHECK_USER, CODE_REFINE_SYSTEM, CODE_REFINE_USER
    from .config import PipelineConfig, CheckerConfig
except ImportError:
    from llm_client import LLMClient
    from pdf_parser import extract_text
    from prompts import CHECK_SYSTEM, CHECK_USER, CODE_REFINE_SYSTEM, CODE_REFINE_USER
    from config import PipelineConfig, CheckerConfig


class CodeChecker:
    def __init__(self, llm_client: LLMClient, config: PipelineConfig):
        self.llm = llm_client
        self.config = config

    def check(self, code: str) -> dict:
        check_items_str = "\n".join(
            f"- {item}" for item in self.config.checker.check_items
        )
        system_prompt = CHECK_SYSTEM.format(check_items=check_items_str)
        user_prompt = CHECK_USER.format(code=code)
        raw = self.llm.chat(system_prompt, user_prompt)
        return self._parse_check_response(raw)

    def refine(
        self, code: str, missing_items: list[dict], paper_chunks: list[dict]
    ) -> str:
        search_keywords = []
        for item in missing_items:
            search_keywords.extend(item.get("search_keywords", []))

        relevant_excerpts = self._search_chunks(paper_chunks, search_keywords)
        excerpts_text = "\n\n---\n\n".join(
            f"[Page {c['page_number']}]: {c['content']}" for c in relevant_excerpts
        )

        missing_text = "\n".join(
            f"- {item['item']}: {item['reason']}" for item in missing_items
        )

        user_prompt = CODE_REFINE_USER.format(
            current_code=code,
            missing_items=missing_text,
            paper_excerpts=excerpts_text,
        )

        raw = self.llm.chat(CODE_REFINE_SYSTEM, user_prompt)
        return self._extract_code(raw)

    def _search_chunks(self, chunks: list[dict], keywords: list[str]) -> list[dict]:
        relevant = []
        seen_pages = set()
        for chunk in chunks:
            content_lower = chunk["content"].lower()
            score = sum(1 for kw in keywords if kw.lower() in content_lower)
            if score > 0:
                relevant.append((score, chunk))
                seen_pages.add(chunk["page_number"])

        if len(relevant) < 3:
            for chunk in chunks:
                if chunk["page_number"] not in seen_pages:
                    for kw in keywords[:3]:
                        if kw.lower() in chunk["content"].lower():
                            relevant.append((0.5, chunk))
                            break

        relevant.sort(key=lambda x: x[0], reverse=True)
        return [c for _, c in relevant[:10]]

    def _parse_check_response(self, raw: str) -> dict:
        text = raw.strip()
        if text.startswith("```"):
            lines = text.split("\n")
            lines = [l for l in lines if not l.startswith("```")]
            text = "\n".join(lines)
        try:
            return json.loads(text)
        except json.JSONDecodeError:
            start = text.find("{")
            end = text.rfind("}") + 1
            if start != -1 and end > start:
                try:
                    return json.loads(text[start:end])
                except json.JSONDecodeError:
                    pass
            return {"is_complete": False, "missing": []}

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
