from pipeline import Pipeline
from config import PipelineConfig

config = PipelineConfig(output_dir="./output")
pipe = Pipeline(config)

result = pipe.run("path/to/your/paper.pdf")
print(f"Code saved to: {result['output_dir']}")
