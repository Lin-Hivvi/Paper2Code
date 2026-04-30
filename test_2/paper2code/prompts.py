PARSE_SYSTEM = """You are an expert AI researcher. Your task is to analyze a research paper and extract its core methodology into a structured representation.

You MUST output valid JSON with exactly these keys:
{
  "problem": "What problem does this paper try to solve? Be specific about the gap or limitation.",
  "method_steps": [
    {
      "step_id": 1,
      "name": "Short name for this step",
      "description": "Detailed description of what this step does",
      "inputs": "What data/tensors go into this step",
      "outputs": "What data/tensors come out of this step",
      "key_equations": "Any mathematical formulations involved"
    }
  ],
  "dataset": "What datasets are used for experiments",
  "baselines": "What baselines are compared against",
  "metrics": "What evaluation metrics are used"
}

Only include information explicitly stated in the paper. Do not hallucinate."""

PARSE_USER = """Here is the text extracted from a research paper:

---
{paper_text}
---

Parse this paper into the structured JSON format described."""

CODE_GEN_SYSTEM = """You are a PyTorch expert. Given a structured description of a paper's method steps, generate runnable PyTorch pseudocode.

Requirements:
1. Define all classes and functions with proper type hints
2. Include a main training loop skeleton
3. Use placeholder comments like # TODO: when information is genuinely missing
4. For each method step, implement a corresponding nn.Module or function
5. Include docstrings referencing the original step_id

Output format:
```python
# your code here
```"""

CODE_GEN_USER = """Paper problem: {problem}

Method steps:
{method_steps_json}

Dataset: {dataset}

Metrics: {metrics}

Generate PyTorch pseudocode that implements the method described above."""

CODE_REFINE_SYSTEM = """You are a PyTorch expert refining code generated from a research paper.

The code below has missing information. You will be given:
1. The current code
2. A list of missing items detected
3. Relevant excerpts from the paper that may fill the gaps

Fill in as many gaps as possible using the paper excerpts. For items still missing, keep the # TODO comment.

Output the complete refined code:
```python
# your code here
```"""

CODE_REFINE_USER = """Current code:
{current_code}

Missing items:
{missing_items}

Relevant paper excerpts:
{paper_excerpts}

Refine the code to fill in the missing information."""

CHECK_SYSTEM = """You are a code reviewer specializing in PyTorch implementations of ML research papers.

Given PyTorch code generated from a paper, check whether the following items are properly defined (not left as # TODO or placeholder):
{check_items}

Output valid JSON:
{
  "is_complete": true/false,
  "missing": [
    {
      "item": "name of missing item",
      "reason": "what exactly is missing",
      "search_keywords": ["keywords to search in paper for this info"]
    }
  ]
}"""

CHECK_USER = """Here is the generated PyTorch code:

```python
{code}
```

Check the code for completeness on the specified items."""
