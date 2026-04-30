import argparse
import json

try:
    from .config import PipelineConfig, LLMConfig, CheckerConfig
    from .pipeline import Pipeline
except ImportError:
    from config import PipelineConfig, LLMConfig, CheckerConfig
    from pipeline import Pipeline


def main():
    parser = argparse.ArgumentParser(
        description="Paper2Code: Parse AI paper -> PyTorch pseudocode"
    )
    parser.add_argument("pdf_path", help="Path to the PDF paper")
    parser.add_argument("--output-dir", default="./output", help="Output directory")
    parser.add_argument("--model", default="gpt-4o", help="LLM model name")
    parser.add_argument(
        "--max-rounds", type=int, default=3, help="Max refinement rounds"
    )
    parser.add_argument(
        "--temperature", type=float, default=0.2, help="LLM temperature"
    )
    args = parser.parse_args()

    config = PipelineConfig(
        llm=LLMConfig(model=args.model, temperature=args.temperature),
        checker=CheckerConfig(max_refinement_rounds=args.max_rounds),
        output_dir=args.output_dir,
    )

    pipe = Pipeline(config)
    result = pipe.run(args.pdf_path)

    print(f"\nResults saved to: {result['output_dir']}")
    print(f"Time elapsed: {result['elapsed_seconds']}s")


if __name__ == "__main__":
    main()
