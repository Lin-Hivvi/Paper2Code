import json
import time
from pathlib import Path

try:
    from .config import PipelineConfig
    from .llm_client import LLMClient
    from .paper_analyzer import PaperAnalyzer
    from .code_generator import CodeGenerator
    from .code_checker import CodeChecker
    from .pdf_parser import extract_text
except ImportError:
    from config import PipelineConfig
    from llm_client import LLMClient
    from paper_analyzer import PaperAnalyzer
    from code_generator import CodeGenerator
    from code_checker import CodeChecker
    from pdf_parser import extract_text


class Pipeline:
    def __init__(self, config: PipelineConfig | None = None):
        self.config = config or PipelineConfig()
        self.llm = LLMClient(self.config.llm)
        self.analyzer = PaperAnalyzer(self.llm, self.config)
        self.generator = CodeGenerator(self.llm, self.config)
        self.checker = CodeChecker(self.llm, self.config)

    def run(self, pdf_path: str) -> dict:
        start_time = time.time()
        pdf_name = Path(pdf_path).stem
        output_dir = Path(self.config.output_dir) / pdf_name
        output_dir.mkdir(parents=True, exist_ok=True)

        print(f"[1/4] Parsing paper: {pdf_path}")
        analysis = self.analyzer.analyze(pdf_path)

        analysis_path = output_dir / "analysis.json"
        with open(analysis_path, "w", encoding="utf-8") as f:
            json.dump(analysis, f, ensure_ascii=False, indent=2)
        print(f"  -> Saved analysis to {analysis_path}")

        print("[2/4] Generating initial PyTorch code...")
        code = self.generator.generate(analysis)

        print("[3/4] Checking and refining code...")
        paper_chunks = extract_text(pdf_path, self.config)
        code = self._refine_loop(code, paper_chunks)

        code_path = output_dir / "model.py"
        with open(code_path, "w", encoding="utf-8") as f:
            f.write(code)
        print(f"  -> Saved code to {code_path}")

        elapsed = time.time() - start_time
        print(f"[4/4] Done! Total time: {elapsed:.1f}s")

        return {
            "analysis": analysis,
            "code": code,
            "output_dir": str(output_dir),
            "elapsed_seconds": round(elapsed, 1),
        }

    def _refine_loop(self, code: str, paper_chunks: list[dict]) -> str:
        for round_num in range(1, self.config.checker.max_refinement_rounds + 1):
            print(
                f"  Refinement round {round_num}/{self.config.checker.max_refinement_rounds}"
            )
            check_result = self.checker.check(code)

            if check_result.get("is_complete", False):
                print("  -> Code is complete, no missing items.")
                break

            missing = check_result.get("missing", [])
            if not missing:
                print("  -> No missing items detected.")
                break

            print(
                f"  -> Found {len(missing)} missing items: {[m['item'] for m in missing]}"
            )
            code = self.checker.refine(code, missing, paper_chunks)

        return code
