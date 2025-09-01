from autogen_core.models import ChatCompletionClient
from autogen_agentchat.agents import AssistantAgent

def client_from_config(llm_config: dict):
    """
    Converts old-style llm_config dict into a ChatCompletionClient compatible object.
    """
    class GenericClient(ChatCompletionClient):
        def __init__(self):
            self.model = llm_config.get("model")
            self.generate_fn = llm_config.get("custom_generate")

        async def create(self, messages, **kwargs):
            config = {"model": self.model, "temperature": llm_config.get("temperature", 0)}
            content = self.generate_fn(messages, config)
            return type("CR", (), {"content": content})

        async def create_stream(self, messages, **kwargs):
            content = self.generate_fn(messages, {"model": self.model})
            yield type("CR", (), {"content": content})

        async def close(self):
            pass

        @property
        def capabilities(self): return {}
        @property
        def model_info(self): return {"name": self.model}
        @property
        def total_usage(self): return {}
        @property
        def actual_usage(self): return {}
        def count_tokens(self, messages): return 0
        @property
        def remaining_tokens(self): return 1_000_000

    return GenericClient()
