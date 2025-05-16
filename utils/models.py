from pydantic import BaseModel, Field
from typing import List, Dict, Optional, Any


class Tool(BaseModel):
    tool_name: str = Field(description="工具名稱")
    tool_type: str = Field(description="工具類型 (函數, API, 數據庫)")
    description: str = Field(description="工具描述")
    parameters: Optional[Dict[str, Any]] = None


class ModelConfig(BaseModel):
    model_name: str = Field(description="模型名稱")
    provider: str = Field(description="模型提供商 (OpenAI, Anthropic, Google等)")
    temperature: float = 0.7
    max_tokens: int = 1000


class AgentConfig(BaseModel):
    agent_name: str = Field(description="Agent名稱")
    agent_description: str = Field(description="Agent描述")
    is_public: bool = False
    llm_config: ModelConfig
    system_prompt: str = Field(description="系統提示詞")
    tools: Optional[List[Tool]] = None
    knowledge_base: Optional[List[str]] = None


class AgentResponse(BaseModel):
    agent_id: str = Field(description="Agent ID")
    agent_name: str = Field(description="Agent名稱")
    status: str = Field(description="狀態")
    message: str = Field(description="消息")
