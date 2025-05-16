import os, json, time
from typing import Optional, List
from litellm import completion

# 工具函式註冊表
TOOL_FUNCTIONS = {}

def register_tool(name=None):
    def decorator(func):
        tool_name = name or func.__name__
        TOOL_FUNCTIONS[tool_name] = func
        return func

    # 支援無參數使用
    if callable(name):
        return decorator(name)
    return decorator

# ✅ 模擬工具：取得天氣
@register_tool()
def get_current_weather(location: str, unit: str = "celsius") -> str:
    return f"{location} 現在天氣是 28 度（單位：{unit}）"

# ✅ Base 類別
class BaseLLM:
    def __init__(self, model: str, api_key: Optional[str] = None, api_base: Optional[str] = None):
        self.model = model
        self.api_key = api_key
        self.api_base = api_base

    def chat(self, prompt: str, stream: bool = False, tools: Optional[List[dict]] = None, tool_choice: Optional[str] = None):
        print(f"[DEBUG] stream = {stream}")

        messages = [{"role": "user", "content": prompt}]
        kwargs = {
            "model": self.model,
            "messages": messages,
        }
        if self.api_key: kwargs["api_key"] = self.api_key
        if self.api_base: kwargs["api_base"] = self.api_base
        if tools: kwargs["tools"] = tools
        if tool_choice: kwargs["tool_choice"] = tool_choice

        # 非 streaming 模式
        if not stream:
            try:
                while True:
                    response = completion(**kwargs)
                    message = response["choices"][0]["message"]

                    if hasattr(message, "tool_calls") and message.tool_calls:
                        for tool_call in message.tool_calls:
                            tool_name = tool_call.function.name
                            args = json.loads(tool_call.function.arguments)

                            tool_func = TOOL_FUNCTIONS.get(tool_name)
                            tool_result = tool_func(**args) if tool_func else f"[No implementation for {tool_name}]"

                            messages.append(message)
                            messages.append({
                                "role": "tool",
                                "tool_call_id": tool_call.id,
                                "content": tool_result
                            })
                            kwargs["messages"] = messages
                    else:
                        return message
            except Exception as e:
                return {"role": "assistant", "content": f"[Error during chat]: {str(e)}"} 

        # ✅ Streaming 模式
        else:
            def stream_generator():
                try:
                    if tools:
                        while True:
                            response = completion(**kwargs)
                            message = response["choices"][0]["message"]

                            if hasattr(message, "tool_calls") and message.tool_calls:
                                for tool_call in message.tool_calls:
                                    tool_name = tool_call.function.name
                                    args = json.loads(tool_call.function.arguments)

                                    tool_func = TOOL_FUNCTIONS.get(tool_name)
                                    tool_result = tool_func(**args) if tool_func else f"[No implementation for {tool_name}]"

                                    messages.append(message)
                                    messages.append({
                                        "role": "tool",
                                        "tool_call_id": tool_call.id,
                                        "content": tool_result
                                    })
                                    kwargs["messages"] = messages
                            else:
                                ans = message.content
                                for i in range(0, len(ans), 2):
                                    yield f"data: {ans[i:i+2]}"
                                    time.sleep(0.05)
                                break
                    else:
                        kwargs["stream"] = True
                        response = completion(**kwargs)
                        for chunk in response:
                            content = chunk["choices"][0]["delta"].get("content", "")
                            if content:
                                yield f"data: {content}"
                except Exception as e:
                    yield f"data: [Error] {str(e)}"
                yield "data: done"

            return stream_generator()


# ✅ 各 LLM 封裝類別
class OpenAIChat(BaseLLM):
    def __init__(self, api_key: str, model: str = "gpt-4.1"):
        os.environ["OPENAI_API_KEY"] = api_key
        super().__init__(model=model, api_key=api_key)

class ClaudeChat(BaseLLM):
    def __init__(self, api_key: str, model: str = "claude-instant-1"):
        os.environ["ANTHROPIC_API_KEY"] = api_key
        super().__init__(model=model, api_key=api_key)

class GeminiChat(BaseLLM):
    def __init__(self, api_key: str, model: str = "gemini-pro"):
        os.environ["GOOGLE_API_KEY"] = api_key
        super().__init__(model=model, api_key=api_key)

class OllamaChat(BaseLLM):
    def __init__(self, model_name: str = "llama3", api_base: str = "http://localhost:11434"):
        super().__init__(model=f"ollama/{model_name}", api_base=api_base)

class HuggingFaceChat(BaseLLM):
    def __init__(self, model_id: str, api_base: str, api_key: str):
        os.environ["HUGGINGFACE_API_KEY"] = api_key
        super().__init__(model=f"huggingface/{model_id}", api_base=api_base, api_key=api_key)

class GrokChat(BaseLLM):
    def __init__(self, api_key: str, model: str = "xai/grok-2-latest"):
        os.environ["XAI_API_KEY"] = api_key
        super().__init__(model=model, api_key=api_key)

class GroqChat(BaseLLM):
    def __init__(self, api_key: str, model: str = "groq/llama3-8b-8192"):
        os.environ["GROQ_API_KEY"] = api_key
        super().__init__(model=model, api_key=api_key)


# ✅ 使用範例
if __name__ == "__main__":
    openai_chat = OpenAIChat(api_key="", model="gpt-4.1")
    prompt = "台北現在天氣如何？"

    tools = [
        {
            "type": "function",
            "function": {
                "name": "get_current_weather",
                "description": "取得指定城市的即時天氣",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "location": {"type": "string", "description": "城市名稱"},
                        "unit": {"type": "string", "enum": ["celsius", "fahrenheit"]}
                    },
                    "required": ["location"]
                }
            }
        }
    ]

    # print("\n--- 非 Streaming 測試 ---")
    # result = openai_chat.chat(prompt="說一個笑話", stream=False)
    # print(result["content"] if isinstance(result, dict) else result.content)

    # print("\n--- Streaming 測試 ---")
    # for chunk in openai_chat.chat(prompt="說一個笑話", stream=True):
    #     print(chunk)

    print("\n--- Function Calling 測試 ---")
    result = openai_chat.chat(prompt=prompt, stream=False, tools=tools, tool_choice="auto")
    print(result["content"] if isinstance(result, dict) else result.content)

    print("\n--- Streaming + Function Calling ---")
    for chunk in openai_chat.chat(prompt=prompt, stream=True, tools=tools, tool_choice="auto"):
        print(chunk)
