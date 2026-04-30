# Paper2Code

把 AI 研究论文 PDF 自动转化为 PyTorch 伪代码的两步流水线工具。

---

## 背景

读 AI 论文特别慢，尤其是方法那部分，反复看好几遍也捋不清作者到底怎么做的，更别说照着复现代码了。一篇论文从读到能跑出一个结果，经常花掉大半个星期六，还容易理解错。

这个工具做的事情很简单：调 GPT 接口做两个事——**解析**和**翻译**，中间加一圈检查循环，缺什么就回论文里找什么。

---

## 工作流程

```
                        ┌──────────────────────────────────────────────┐
                        │             Paper2Code 流水线                 │
                        └──────────────────────────────────────────────┘

  输入                     阶段一：解析                      阶段二：翻译
 ┌──────┐   提取文字    ┌──────────────┐   结构化 JSON   ┌──────────────┐
 │  PDF │ ────────────► │  结构化解析   │ ─────────────► │  PyTorch 生码 │
 └──────┘              └──────────────┘                 └──────┬───────┘
                                                              │
                                                              ▼
                     ┌─────────────────────────────────────────────────┐
                     │              阶段三：检查-精修循环                  │
                     │                                                 │
                     │    ┌──────────┐    缺项     ┌──────────────┐     │
                     │    │  代码检查  │ ────────► │  回查论文原文  │     │
                     │    └────┬─────┘           └──────┬───────┘     │
                     │         │                        │             │
                     │         │ 完整                    ▼             │
                     │         │                  ┌──────────────┐    │
                     │         │                  │  GPT 精修代码  │    │
                     │         │                  └──────┬───────┘    │
                     │         │                         │            │
                     │         │          ┌──────────────┘            │
                     │         │          │  重复直到完整或达到最大轮数  │
                     │         ▼          ▼                           │
                     │    输出 model.py                               │
                     └─────────────────────────────────────────────────┘
```

### 阶段一：解析（Parse）

从 PDF 提取文字后，让 GPT 按固定结构拆成 JSON：

| 字段 | 说明 |
|---|---|
| `problem` | 论文要解决什么问题 |
| `method_steps` | 方法分几步，每步含名称、描述、输入、输出、关键公式 |
| `dataset` | 用什么数据集 |
| `baselines` | 和哪些基线对比 |
| `metrics` | 用什么评估指标 |

对于长论文（超过 ~12000 字符），会先对前 6 个文本块做首轮解析，再单独提取方法章节的文本块进行二次精炼，合并得到最终结果。

### 阶段二：翻译（Translate）

把结构化 JSON 中的 `method_steps` 翻译成 PyTorch 伪代码。每个步骤对应一个 `nn.Module` 或函数，附带 docstring 引用原始 `step_id`。信息不足的地方以 `# TODO` 标记。

### 阶段三：检查-精修循环（Check & Refine）

生成初版代码后，进入最多 3 轮的检查循环：

1. **检查**：让 GPT 逐项检查代码中是否缺少关键定义（输入维度、损失函数、优化器等），返回缺项列表和对应的搜索关键词
2. **回查原文**：根据缺项的搜索关键词，在之前分块的论文文本中做关键词匹配，找到最相关的 10 个文本块
3. **精修**：把当前代码 + 缺项列表 + 相关原文片段一起交给 GPT，补全缺失信息

如果代码检查结果为"完整"，或达到最大轮数，则停止循环。

---

## 实测效果

在 8 篇图神经网络论文上自测：

| 指标 | 手动复现 | 使用本工具 |
|---|---|---|
| 单篇耗时 | 4-5 小时 | ~1.5 小时 |
| 成功率 | — | ~70% |

成功率约 70%，主要失败原因是论文方法描述过于模糊或缺少关键实现细节，GPT 无论怎么回查原文也找不到。

---

## 安装

### 1. 克隆项目

```bash
git clone <repo-url>
cd paper2code
```

### 2. 安装依赖

```bash
python -m pip install -r requirements.txt
```

依赖清单：

| 包名 | 用途 |
|---|---|
| `openai` | 调用 GPT API |
| `langchain` | 文档处理框架 |
| `langchain-community` | PDF 加载器（PyPDFLoader） |
| `langchain-text-splitters` | 文本分块（RecursiveCharacterTextSplitter） |
| `pypdf` | PDF 底层解析 |

> **注意**：如果你的系统有多个 Python（如 Anaconda + 独立安装版），请确保用实际运行项目的那个 Python 来安装依赖。可以先用 `where python` 查看有哪些 Python，然后用完整路径安装，例如：
>
> ```bash
> "C:\Users\你的用户名\AppData\Local\Programs\Python\Python313\python.exe" -m pip install -r requirements.txt
> ```

### 3. 配置 API Key

必须设置 `OPENAI_API_KEY`，否则运行时会报错。

**Linux / macOS：**

```bash
export OPENAI_API_KEY="sk-xxxxxxxx"
```

**Windows CMD：**

```cmd
set OPENAI_API_KEY=sk-xxxxxxxx
```

**Windows PowerShell：**

```powershell
$env:OPENAI_API_KEY = "sk-xxxxxxxx"
```

如果使用第三方中转 API（如 Azure OpenAI、国内中转站），还需设置 `OPENAI_BASE_URL`：

```powershell
$env:OPENAI_BASE_URL = "https://your-proxy.example.com/v1"
```

也可以在 Python 代码中直接传入配置而不用环境变量，见下方高级用法。

---

## 使用方法

### 方式一：命令行运行

```bash
# 基本用法
python -m paper2code "C:\Users\Jane Doe\Downloads\some_paper.pdf"

# 或者直接运行 __main__.py
python "C:\Users\Jane Doe\Desktop\test_2\paper2code\__main__.py" "C:\Users\Jane Doe\Downloads\some_paper.pdf"
```

**完整参数说明：**

```
python -m paper2code pdf_path [--output-dir DIR] [--model MODEL] [--max-rounds N] [--temperature T]
```

| 参数 | 必填 | 默认值 | 说明 |
|---|---|---|---|
| `pdf_path` | 是 | — | 论文 PDF 文件的路径 |
| `--output-dir` | 否 | `./output` | 输出目录，结果会存到该目录下以论文名命名的子文件夹 |
| `--model` | 否 | `gpt-4o` | 使用的 LLM 模型名称，如 `gpt-4o`、`gpt-4o-mini` |
| `--max-rounds` | 否 | `3` | 检查-精修循环的最大轮数，增大可提高完整度但更费 token |
| `--temperature` | 否 | `0.2` | 生成温度，建议保持低值以获得更确定性的输出 |

**示例：**

```bash
# 使用 gpt-4o-mini 省钱，精修 5 轮提高完整度
python -m paper2code paper.pdf --model gpt-4o-mini --max-rounds 5

# 指定输出目录
python -m paper2code paper.pdf --output-dir ./my_results
```

### 方式二：Python 代码调用

适合在自己的脚本或 Notebook 中集成：

```python
from paper2code.config import PipelineConfig, LLMConfig, CheckerConfig
from paper2code.pipeline import Pipeline

# 基本用法 —— 从环境变量读取 API Key
config = PipelineConfig(
    output_dir="./output",
)
pipe = Pipeline(config)
result = pipe.run("path/to/paper.pdf")

print(f"分析结果: {result['output_dir']}/analysis.json")
print(f"生成代码: {result['output_dir']}/model.py")
print(f"耗时: {result['elapsed_seconds']}s")
```

```python
# 高级用法 —— 在代码中指定 API Key 和自定义配置
config = PipelineConfig(
    llm=LLMConfig(
        api_key="sk-xxxxxxxx",             # 直接传 Key，不用设环境变量
        base_url="https://api.example.com/v1",  # 第三方 API 地址
        model="gpt-4o",
        temperature=0.2,
        max_tokens=4096,
    ),
    checker=CheckerConfig(
        max_refinement_rounds=3,
        check_items=[                       # 自定义检查项
            "input_dimensions",
            "loss_function",
            "optimizer",
            "activation_function",
            "layer_dimensions",
            "hyperparameters",
        ],
    ),
    output_dir="./output",
    pdf_chunk_size=3000,                    # PDF 分块大小（字符数）
    pdf_chunk_overlap=500,                  # 分块重叠（字符数）
)

pipe = Pipeline(config)
result = pipe.run("path/to/paper.pdf")
```

### 运行输出示例

```
[1/4] Parsing paper: paper.pdf
  -> Saved analysis to output\paper\analysis.json
[2/4] Generating initial PyTorch code...
[3/4] Checking and refining code...
  Refinement round 1/3
  -> Found 3 missing items: ['input_dimensions', 'loss_function', 'optimizer']
  Refinement round 2/3
  -> Found 1 missing items: ['hyperparameters']
  Refinement round 3/3
  -> Code is complete, no missing items.
  -> Saved code to output\paper\model.py
[4/4] Done! Total time: 85.3s

Results saved to: output\paper
Time elapsed: 85.3s
```

---

## 输出文件

运行后在 `output/<论文名>/` 目录下生成两个文件：

### analysis.json —— 论文结构化解析

```json
{
  "problem": "现有图神经网络在节点分类任务上存在过平滑问题...",
  "method_steps": [
    {
      "step_id": 1,
      "name": "Feature Transformation",
      "description": "对输入节点特征做线性变换...",
      "inputs": "节点特征矩阵 X ∈ R^{N×F}",
      "outputs": "变换后特征 H ∈ R^{N×D}",
      "key_equations": "H = XW + b"
    },
    {
      "step_id": 2,
      "name": "Message Passing",
      "description": "在图结构上进行消息传递与聚合...",
      "inputs": "变换后特征 H, 邻接矩阵 A",
      "outputs": "聚合后特征 H'",
      "key_equations": "H' = σ(ÂHΘ)"
    }
  ],
  "dataset": "Cora, Citeseer, Pubmed",
  "baselines": "GCN, GAT, GraphSAGE",
  "metrics": "Accuracy, F1-score",
  "source_pdf": "paper.pdf",
  "chunks_count": 18
}
```

### model.py —— PyTorch 伪代码

```python
import torch
import torch.nn as nn
import torch.nn.functional as F


class FeatureTransformation(nn.Module):
    """Step 1: Feature Transformation"""

    def __init__(self, in_features: int, out_features: int):
        super().__init__()
        self.linear = nn.Linear(in_features, out_features)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        return self.linear(x)


class MessagePassing(nn.Module):
    """Step 2: Message Passing"""

    def __init__(self, in_features: int, out_features: int):
        super().__init__()
        self.theta = nn.Parameter(torch.randn(in_features, out_features))

    def forward(self, h: torch.Tensor, adj: torch.Tensor) -> torch.Tensor:
        support = torch.matmul(h, self.theta)
        out = torch.matmul(adj, support)
        return F.relu(out)


class PaperModel(nn.Module):
    def __init__(self, num_features: int, hidden_dim: int, num_classes: int):
        super().__init__()
        self.step1 = FeatureTransformation(num_features, hidden_dim)
        self.step2 = MessagePassing(hidden_dim, num_classes)

    def forward(self, x: torch.Tensor, adj: torch.Tensor) -> torch.Tensor:
        h = self.step1(x)
        h = self.step2(h, adj)
        return F.log_softmax(h, dim=1)


def train(model, data, adj, optimizer, criterion, epochs=200):
    model.train()
    for epoch in range(epochs):
        optimizer.zero_grad()
        output = model(data.x, adj)
        loss = criterion(output[data.train_mask], data.y[data.train_mask])
        loss.backward()
        optimizer.step()


if __name__ == "__main__":
    model = PaperModel(num_features=1433, hidden_dim=64, num_classes=7)
    optimizer = torch.optim.Adam(model.parameters(), lr=0.01, weight_decay=5e-4)
    criterion = nn.NLLLoss()
```

> 生成的是**伪代码**，基本结构和方法步骤是对的，但数据加载、具体训练流程仍需根据实际情况人工调整。

---

## 项目结构

```
paper2code/
├── __init__.py           # 包入口，导出 Pipeline / PipelineConfig / LLMConfig / CheckerConfig
├── __main__.py           # CLI 入口，支持 python -m paper2code 和直接运行
├── config.py             # 三个 dataclass 配置类
│   ├── LLMConfig         #   API Key、基础 URL、模型名、温度、最大 token
│   ├── CheckerConfig     #   最大精修轮数、检查项列表
│   └── PipelineConfig    #   LLM/Checker 配置、输出目录、PDF 分块参数
├── pdf_parser.py         # PDF 文本提取与分块
│   ├── extract_text()    #   加载 PDF → 按页分块返回 list[dict]
│   └── load_full_text()  #   加载 PDF → 返回完整文本字符串
├── llm_client.py         # GPT API 封装
│   ├── LLMClient.chat()  #   单轮对话（system + user）
│   └── chat_with_history()#  多轮对话
├── prompts.py            # 四套 Prompt 模板
│   ├── PARSE_SYSTEM/USER #   阶段一：论文 → 结构化 JSON
│   ├── CODE_GEN_SYSTEM/USER# 阶段二：JSON → PyTorch 代码
│   ├── CHECK_SYSTEM/USER #   阶段三a：检查代码缺项
│   └── REFINE_SYSTEM/USER#   阶段三b：根据原文精修代码
├── paper_analyzer.py     # 阶段一实现
│   ├── analyze()         #   主方法：短论文单次解析，长论文分段解析+合并
│   ├── _analyze_in_sections()#  长论文：先解析前6块，再单独提取方法章节精炼
│   └── _extract_method_chunks()# 按关键词定位方法章节的文本块
├── code_generator.py     # 阶段二实现
│   └── generate()        #   接收 analysis dict → 输出 PyTorch 代码字符串
├── code_checker.py       # 阶段三实现
│   ├── check()           #   检查代码缺项 → 返回 {is_complete, missing[]}
│   ├── refine()          #   根据缺项回查原文 → GPT 精修代码
│   └── _search_chunks()  #   按关键词给文本块打分，返回最相关的10块
├── pipeline.py           # 主流水线编排
│   └── run()             #   串联三阶段：解析 → 生码 → 检查精修循环
├── example.py            # 最简单的调用示例
└── requirements.txt      # 依赖清单
```

---

## 配置详解

### LLMConfig

| 字段 | 类型 | 默认值 | 说明 |
|---|---|---|---|
| `api_key` | str | 环境变量 `OPENAI_API_KEY` | OpenAI API 密钥 |
| `base_url` | str | 环境变量 `OPENAI_BASE_URL`，默认 `https://api.openai.com/v1` | API 基础地址 |
| `model` | str | `gpt-4o` | 模型名称 |
| `temperature` | float | `0.2` | 生成温度 |
| `max_tokens` | int | `4096` | 单次生成最大 token 数 |

### CheckerConfig

| 字段 | 类型 | 默认值 | 说明 |
|---|---|---|---|
| `max_refinement_rounds` | int | `3` | 检查-精修最大循环次数 |
| `check_items` | list[str] | 见下方 | 检查哪些关键项是否在代码中定义 |

默认检查项：

| 检查项 | 含义 |
|---|---|
| `input_dimensions` | 输入张量的维度定义 |
| `loss_function` | 损失函数 |
| `optimizer` | 优化器 |
| `activation_function` | 激活函数 |
| `layer_dimensions` | 各层维度 |
| `hyperparameters` | 学习率、权重衰减等超参数 |

### PipelineConfig

| 字段 | 类型 | 默认值 | 说明 |
|---|---|---|---|
| `llm` | LLMConfig | — | LLM 配置 |
| `checker` | CheckerConfig | — | 检查器配置 |
| `output_dir` | str | `./output` | 输出根目录 |
| `pdf_chunk_size` | int | `3000` | PDF 文本分块大小（字符数） |
| `pdf_chunk_overlap` | int | `500` | 分块重叠大小（字符数） |

---

## 常见问题

### Q: 运行报 `OPENAI_API_KEY is not set`

需要先设置 API Key 环境变量，或在代码中直接传入：

```python
from paper2code.config import LLMConfig, PipelineConfig
config = PipelineConfig(llm=LLMConfig(api_key="sk-xxxxxxxx"))
```

### Q: 运行报 `No module named 'xxx'`

依赖没有装到正确的 Python 环境里。检查你实际用的是哪个 Python：

```bash
where python
```

然后用那个路径安装依赖：

```bash
"C:\实际使用的\python.exe" -m pip install -r requirements.txt
```

### Q: `pip.exe` 无法运行 / 拒绝访问

不要直接用 `pip.exe`，改用 `python -m pip`：

```bash
python -m pip install -r requirements.txt
```

### Q: 运行报 `ImportError: attempted relative import with no known parent package`

不要直接用 `python paper2code/__main__.py` 运行子目录中的文件。请用以下任一方式：

```bash
# 方式一：从项目根目录用模块方式运行
cd C:\Users\Jane Doe\Desktop\test_2
python -m paper2code paper.pdf

# 方式二：用完整路径运行 __main__.py（已兼容）
python "C:\Users\Jane Doe\Desktop\test_2\paper2code\__main__.py" paper.pdf
```

### Q: 生成的代码能直接跑吗？

不能。生成的是**伪代码骨架**，方法步骤和整体结构是对的，但数据加载、具体训练流程、超参数调优等仍需人工补充。工具的价值在于帮你快速理解论文方法、搭出代码框架，省去从零开始读论文写代码的时间。

### Q: 成功率为什么只有 70%？

主要失败原因：
- 论文方法章节描述过于笼统，缺少具体的维度、公式或实现细节
- 论文的创新点依赖某些 tricks（如特殊的初始化、梯度裁剪方式）没有在正文中明确写出
- GPT 解析公式时偶尔出错，尤其是复杂的数学推导

建议：
- 使用 GPT-4o 及以上模型，小模型对公式和步骤的解析能力明显不足
- 适当增大 `--max-rounds`（如 5），多轮精修有机会补回更多细节
- 对生成结果做人工审查，尤其是损失函数和维度部分

### Q: 支持非 OpenAI 的模型吗？

支持任何兼容 OpenAI API 格式的服务，只需设置 `base_url`：

```python
from paper2code.config import LLMConfig, PipelineConfig
config = PipelineConfig(
    llm=LLMConfig(
        api_key="your-key",
        base_url="https://your-service.com/v1",
        model="your-model-name",
    )
)
```

---

## License

MIT
