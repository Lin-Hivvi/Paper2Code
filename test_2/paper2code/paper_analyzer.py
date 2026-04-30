import json

try:
    from .llm_client import LLMClient
    from .pdf_parser import extract_text
    from .prompts import PARSE_SYSTEM, PARSE_USER
    from .config import PipelineConfig
except ImportError:
    from llm_client import LLMClient
    from pdf_parser import extract_text
    from prompts import PARSE_SYSTEM, PARSE_USER
    from config import PipelineConfig


class PaperAnalyzer:
    def __init__(self, llm_client: LLMClient, config: PipelineConfig):
        self.llm = llm_client
        self.config = config

    def analyze(self, pdf_path: str) -> dict:
        chunks = extract_text(pdf_path, self.config)
        full_text = "\n\n".join(c["content"] for c in chunks)

        if len(full_text) > 12000:
            analysis = self._analyze_in_sections(chunks, full_text)
        else:
            analysis = self._analyze_single(full_text)

        analysis["source_pdf"] = pdf_path
        analysis["chunks_count"] = len(chunks)
        return analysis

    def _analyze_single(self, text: str) -> dict:
        user_prompt = PARSE_USER.format(paper_text=text)
        raw = self.llm.chat(PARSE_SYSTEM, user_prompt)
        return self._parse_json_response(raw)

    def _analyze_in_sections(self, chunks: list[dict], full_text: str) -> dict:
        first_pass_text = "\n\n".join(c["content"] for c in chunks[:6])
        user_prompt = PARSE_USER.format(paper_text=first_pass_text)
        raw = self.llm.chat(PARSE_SYSTEM, user_prompt)
        result = self._parse_json_response(raw)

        method_section = self._extract_method_chunks(chunks)
        if method_section:
            method_text = "\n\n".join(c["content"] for c in method_section)
            refine_prompt = (
                "Here is an initial parsing of a paper:\n"
                f"{json.dumps(result, ensure_ascii=False, indent=2)}\n\n"
                "Now here is additional text from the method section that may contain more detail:\n"
                f"---\n{method_text}\n---\n\n"
                "Refine the method_steps using this additional information. "
                "Output the complete refined JSON in the same format."
            )
            raw = self.llm.chat(PARSE_SYSTEM, refine_prompt)
            result = self._parse_json_response(raw)

        return result

    def _extract_method_chunks(self, chunks: list[dict]) -> list[dict]:
        method_keywords = [
            "method",
            "approach",
            "proposed",
            "framework",
            "architecture",
            "model",
            "3 ",
            "4 ",
            "3.",
            "4.",
        ]
        method_chunks = []
        capture = False
        for chunk in chunks:
            content_lower = chunk["content"].lower()
            if any(kw in content_lower[:80] for kw in method_keywords):
                capture = True
            if capture:
                method_chunks.append(chunk)
            if any(
                kw in content_lower[:80]
                for kw in ["experiment", "evaluation", "5", "6"]
            ):
                if capture:
                    break
        return method_chunks

    def _parse_json_response(self, raw: str) -> dict:
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
            return {
                "problem": "Failed to parse LLM response",
                "method_steps": [],
                "dataset": "",
                "baselines": "",
                "metrics": "",
                "raw_response": text,
            }
