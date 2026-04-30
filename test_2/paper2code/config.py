import os
from dataclasses import dataclass, field


@dataclass
class LLMConfig:
    api_key: str = os.getenv("OPENAI_API_KEY", "")
    base_url: str = os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1")
    model: str = "gpt-4o"
    temperature: float = 0.2
    max_tokens: int = 4096


@dataclass
class CheckerConfig:
    max_refinement_rounds: int = 3
    check_items: list = field(default_factory=lambda: [
        "input_dimensions",
        "loss_function",
        "optimizer",
        "activation_function",
        "layer_dimensions",
        "hyperparameters",
    ])


@dataclass
class PipelineConfig:
    llm: LLMConfig = field(default_factory=LLMConfig)
    checker: CheckerConfig = field(default_factory=CheckerConfig)
    output_dir: str = "./output"
    pdf_chunk_size: int = 3000
    pdf_chunk_overlap: int = 500
