from app.llm.openai_compatible import OpenAICompatibleProvider


class OpenAIProvider(OpenAICompatibleProvider):
    def __init__(self, api_key: str, base_url: str):
        super().__init__(name="openai", api_key=api_key, base_url=base_url)
