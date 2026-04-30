from openai import OpenAI

try:
    from .config import LLMConfig
except ImportError:
    from config import LLMConfig


class LLMClient:
    def __init__(self, config: LLMConfig | None = None):
        self.config = config or LLMConfig()
        if not self.config.api_key:
            raise ValueError("OPENAI_API_KEY is not set. Set it via env var or config.")
        self.client = OpenAI(
            api_key=self.config.api_key,
            base_url=self.config.base_url,
        )

    def chat(self, system_prompt: str, user_prompt: str) -> str:
        response = self.client.chat.completions.create(
            model=self.config.model,
            temperature=self.config.temperature,
            max_tokens=self.config.max_tokens,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
        )
        return response.choices[0].message.content

    def chat_with_history(self, messages: list[dict]) -> str:
        response = self.client.chat.completions.create(
            model=self.config.model,
            temperature=self.config.temperature,
            max_tokens=self.config.max_tokens,
            messages=messages,
        )
        return response.choices[0].message.content
