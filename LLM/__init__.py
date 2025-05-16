import os
from .base import BaseLLM, completion

class OpenAIChat(BaseLLM):
    def __init__(self,
                 model_name: str = 'gpt-4.1',
                 api_key: str = None,
                 api_base: str = None,
                 temperature: float = 0.6,
                 max_tokens: int = 1500):
        os.environ['OPENAI_API_KEY'] = api_key or os.getenv('OPENAI_API_KEY')
        super().__init__(provider='openai',
                         model_name=model_name,
                         api_key=api_key,
                         api_base=api_base,
                         temperature=temperature,
                         max_tokens=max_tokens)

class ClaudeChat(BaseLLM):
    def __init__(self,
                 model_name: str = 'claude-3-7-sonnet-20250219',
                 api_key: str = None,
                 api_base: str = None,
                 temperature: float = 0.6,
                 max_tokens: int = 1500):
        os.environ['ANTHROPIC_API_KEY'] = api_key or os.getenv('ANTHROPIC_API_KEY')
        super().__init__(provider='anthropic',
                         model_name=model_name,
                         api_key=api_key,
                         api_base=api_base,
                         temperature=temperature,
                         max_tokens=max_tokens)


class GeminiChat(BaseLLM):   
    def __init__(self,
                 model_name: str = 'gemini/gemini-2.5-pro-exp-03-25',
                 api_key: str = None,
                 api_base: str = None,
                 temperature: float = 0.6,
                 max_tokens: int = 1500):
        os.environ['ANTHROPIC_API_KEY'] = api_key or os.getenv('ANTHROPIC_API_KEY')
        super().__init__(provider='google',
                         model_name=model_name,
                         api_key=api_key,
                         api_base=api_base,
                         temperature=temperature,
                         max_tokens=max_tokens)

class OllamaChat(BaseLLM):    
    def __init__(self,
                 model_name: str = 'ollama/llama3:70b',
                 api_key: str = None,
                 api_base: str = "http://localhost:11434",
                 temperature: float = 0.6,
                 max_tokens: int = 1500):

        super().__init__(provider='ollama',
                         model_name=model_name,
                         api_key=api_key,
                         api_base=api_base,
                         temperature=temperature,
                         max_tokens=max_tokens)

class HuggingFaceChat(BaseLLM):        
    def __init__(self,
                 model_name: str = 'llama4',
                 api_key: str = None,
                 api_base: str = None,
                 temperature: float = 0.6,
                 max_tokens: int = 1500):

        os.environ['HUGGINGFACE_API_KEY'] = api_key or os.getenv('HUGGINGFACE_API_KEY')
        super().__init__(provider='huggingface',
                         model_name=f"huggingface/{model_name}",
                         api_key=api_key,
                         api_base=api_base,
                         temperature=temperature,
                         max_tokens=max_tokens)

class GrokChat(BaseLLM):        
    def __init__(self,
                 model_name: str = 'xai/grok-3-fast-latest',
                 api_key: str = None,
                 api_base: str = None,
                 temperature: float = 0.6,
                 max_tokens: int = 1500):
        os.environ['XAI_API_KEY'] = api_key or os.getenv('XAI_API_KEY')
        super().__init__(provider='grok',
                         model_name=model_name,
                         api_key=api_key,
                         api_base=api_base,
                         temperature=temperature,
                         max_tokens=max_tokens)

class GroqChat(BaseLLM):    
    def __init__(self,
                 model_name: str = 'groq/llama-3.3-70b-versatile',
                 api_key: str = None,
                 api_base: str = None,
                 temperature: float = 0.6,
                 max_tokens: int = 1500):
        os.environ['GROQ_API_KEY'] = api_key or os.getenv('GROQ_API_KEY')
        super().__init__(provider='groq',
                         model_name=model_name,
                         api_key=api_key,
                         api_base=api_base,
                         temperature=temperature,
                         max_tokens=max_tokens)


# 若要支援更多 provider，可自行新增對應子類與 mapping
def get_llm(provider: str,
             model_name: str,
             api_key: str = None,
             api_base: str = None,
             temperature: float = 0.6,
             max_tokens: int = 1500) -> BaseLLM:
    mapping = {
        'openai': OpenAIChat,
        'anthropic': ClaudeChat,
        'google': GeminiChat,
        'ollama': OllamaChat,
        'huggingface': HuggingFaceChat,
        'grok': GrokChat,
        'groq': GroqChat,
    }
    cls = mapping.get(provider.lower())
    if not cls:
        raise ValueError(f"Unknown LLM provider: {provider}")
    return cls(model_name=model_name,
               api_key=api_key,
               api_base=api_base,
               temperature=temperature,
               max_tokens=max_tokens)
