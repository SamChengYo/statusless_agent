import os
import json
import logging
from LLM import get_llm
from Tool import TOOL_FUNCTIONS, register_tool
from Tool.formatter import generate_tool_schema
from fastapi import FastAPI, HTTPException, Body
from pydantic import BaseModel, Field
from typing import List, Dict, Optional, Literal
from fastapi.responses import StreamingResponse
from utils.decrypt import get_key, lock_key
from fastapi import FastAPI, HTTPException, Body, Depends
import secrets
import random
import string
import requests
from fastapi.middleware.cors import CORSMiddleware

# 確保 tools 目錄存在
os.makedirs(os.path.join('Tool', 'tools'), exist_ok=True)

def generate_id():
    letters = ''.join(random.choices(string.ascii_uppercase, k=4))
    hex_part = secrets.token_hex(2)
    
    return f"{letters}-{hex_part}"

def load_agent_config(agent_id: str) -> dict:
    path = os.path.join('agents', f'{agent_id}.json')
    with open(path, 'r', encoding='utf-8') as f:
        return json.load(f)

def save_agent_config(agent_id: str, config: dict):
    path = os.path.join('agents', f'{agent_id}.json')
    with open(path, 'w', encoding='utf-8') as f:
        json.dump(config, f, ensure_ascii=False, indent=2)



class LLMConfig(BaseModel):
    model_name: str
    provider: str
    temperature: float
    max_tokens: int
    api_base: Optional[str] = None

class QueryRequest(BaseModel):
    agent_id: str
    llm_config: LLMConfig
    user_query: str
    streaming: bool = False
    system_prompt: Optional[str] = "你是一個熱心助人的幫手。"
    history: List[Dict] = []
    password: str


# 動態工具規格模型
class ToolSpec(BaseModel):
    type: Literal['function', 'api', 'select']
    name: str
    content: str = ""  # function 類型為代碼，api 類型為 URL，select 類型可為空
    description: Optional[str] = None  # api 類型的註解

class APIKeysConfig(BaseModel):
    openai: str = ""
    anthropic: str = ""
    google: str = ""
    huggingface: str = ""
    grok: str = ""
    groq: str = ""

class AgentConfig(BaseModel):
    name: str
    description: str
    is_public: bool
    system_prompt: str
    tools: List[ToolSpec]
    knowledge_base: str
    api_keys: APIKeysConfig = Field(default_factory=APIKeysConfig)
    password: Optional[str] = None  # 用於加密 API 密鑰

# 用於部分更新的模型
class AgentConfigUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    is_public: Optional[bool] = None
    system_prompt: Optional[str] = None
    tools: Optional[List[str]] = None  # 只接受工具名稱的列表，用於啟用/禁用工具
    knowledge_base: Optional[str] = None
    api_keys: Optional[APIKeysConfig] = None
    password: Optional[str] = None  # 用於加密 API 密鑰

app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

def write_tool_file(spec: ToolSpec):
    """根據規格創建或覆蓋工具模組文件"""
    path = os.path.join('Tool', 'tools', f"{spec.name}.py")
    if spec.type == 'function':
        # 將提供的函數代碼包裝在 register_tool 裝飾器中
        content = spec.content.strip()
        # 確保函數定義保持完整
        module_code = f"""from Tool import register_tool

@register_tool()
{content}
"""
    else:  # api 類型
        url = spec.content.strip()
        description = spec.description or f"調用外部 API {url} 並傳入參數"
        module_code = f"""import requests
from Tool import register_tool

@register_tool()
def {spec.name}(**params):
    \"\"\"{description}\"\"\"
    response = requests.get("{url}", params=params)
    response.raise_for_status()
    return response.json()
"""
    with open(path, 'w', encoding='utf-8') as f:
        f.write(module_code)

def remove_tool_file(name: str):
    """如果存在則刪除工具模組文件"""
    path = os.path.join('Tool', 'tools', f"{name}.py")
    if os.path.exists(path):
        os.remove(path)

@app.post("/chat")
async def chat(request: QueryRequest):
    try:
        cfg = load_agent_config(request.agent_id)
        
        try:
            encrypt_key = cfg['api_keys'][request.llm_config.provider]
            api_key = get_key(encrypt_key,request.password)
        except:
            api_key = None
        
        
        llm = get_llm(
            provider=request.llm_config.provider,
            model_name=request.llm_config.model_name,
            api_key=api_key,
            api_base=request.llm_config.api_base,
            temperature=request.llm_config.temperature,
            max_tokens=request.llm_config.max_tokens
        )

        selected = [TOOL_FUNCTIONS[name] for name in cfg['tools'] if name in TOOL_FUNCTIONS]
        tool_schemas = generate_tool_schema(selected)

        if request.streaming:
            def stream():
                gen = llm.chat(
                    system_prompt=request.system_prompt,
                    user_prompt=request.user_query,
                    tools=tool_schemas,
                    history=request.history,
                    stream=True
                )
                for chunk in gen:
                    yield f"{chunk}\n"
            return StreamingResponse(stream(), media_type="text/event-stream")
        else:    
            response = llm.chat(
                system_prompt=request.system_prompt,
                user_prompt=request.user_query,
                tools=tool_schemas,
                history=request.history,
                stream=request.streaming
            )

            return {"response": response}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/agent")
async def create_agent(config: AgentConfig):
    agent_id = generate_id()
    
    # 處理工具文件並收集名稱
    tool_names = []
    for spec in config.tools:
        if spec.type == 'select':
            # 檢查工具是否存在
            path = os.path.join('Tool', 'tools', f"{spec.name}.py")
            if os.path.exists(path):
                tool_names.append(spec.name)
        else:
            # 創建新工具
            write_tool_file(spec)
            tool_names.append(spec.name)
    
    # 準備並保存代理配置（tools 中只保存名稱）
    agent_data = config.model_dump(exclude={"password"})
    agent_data["id"] = agent_id
    agent_data["tools"] = tool_names
    
    # 加密 API 密鑰
    if config.password and "api_keys" in agent_data and agent_data["api_keys"]:
        for provider, key in agent_data["api_keys"].items():
            if key:  # 只加密非空的密鑰
                try:
                    encrypted_key = lock_key(key, config.password)
                    if encrypted_key is None:
                        agent_data["api_keys"][provider] = f"ENCRYPTION_FAILED"
                    else:
                        agent_data["api_keys"][provider] = encrypted_key
                except Exception as e:
                    agent_data["api_keys"][provider] = f"ENCRYPTION_ERROR"
    
    os.makedirs('agents', exist_ok=True)
    path = os.path.join("agents", f"{agent_id}.json")
    with open(path, "w", encoding="utf-8") as f:
        json.dump(agent_data, f, ensure_ascii=False, indent=2)

    return {"message": "Agent created", "agent_id": agent_id}

@app.put("/agent/{agent_id}")
async def update_agent(agent_id: str, config_update: AgentConfigUpdate):
    path = os.path.join("agents", f"{agent_id}.json")
    if not os.path.exists(path):
        raise HTTPException(status_code=404, detail="Agent not found")
    
    # 載入現有配置
    old_cfg = load_agent_config(agent_id)
    
    # 準備更新後的配置
    updated_cfg = old_cfg.copy()
    
    # 更新提供的字段
    update_data = {k: v for k, v in config_update.model_dump(exclude_unset=True).items() if v is not None}
    
    # 特殊處理 api_keys，允許部分更新並加密
    if 'api_keys' in update_data and isinstance(update_data['api_keys'], dict):
        if 'api_keys' not in updated_cfg:
            updated_cfg['api_keys'] = {}
        
        # 獲取密碼
        password = config_update.password
        
        for provider, key in update_data['api_keys'].items():
            if key: 
                if password:
                    try:
                        encrypted_key = lock_key(key, password)
                        if encrypted_key is None:
                            updated_cfg['api_keys'][provider] = f"ENCRYPTION_FAILED:{key}"
                        else:
                            updated_cfg['api_keys'][provider] = encrypted_key
                    except Exception as e:
                        updated_cfg['api_keys'][provider] = f"ENCRYPTION_ERROR"
                else:
                    updated_cfg['api_keys'][provider] = key
            else:
                updated_cfg['api_keys'][provider] = ""
        
        del update_data['api_keys']
    
    # 更新其他字段
    updated_cfg.update(update_data)
    
    # 處理工具啟用/禁用
    if config_update.tools is not None:
        # 只更新工具列表，不修改工具內容
        updated_cfg["tools"] = config_update.tools
    
    # 保存更新後的配置
    with open(path, "w", encoding="utf-8") as f:
        json.dump(updated_cfg, f, ensure_ascii=False, indent=2)

    return {"message": "Agent updated", "agent_id": agent_id}

# 新增工具端點
@app.post("/tool")
async def create_tool(spec: ToolSpec):
    """創建新工具"""
    if spec.type == 'select':
        # 檢查工具是否存在
        path = os.path.join('Tool', 'tools', f"{spec.name}.py")
        if not os.path.exists(path):
            raise HTTPException(status_code=404, detail="Tool not found")
        return {"message": "Tool selected", "name": spec.name}
    else:
        # 創建新工具
        write_tool_file(spec)
        return {"message": "Tool created", "name": spec.name}

@app.put("/tool/{name}")
async def update_tool(name: str, spec: ToolSpec):
    """更新現有工具"""
    if spec.name != name:
        raise HTTPException(status_code=400, detail="Tool name mismatch")
    
    # 檢查工具是否存在
    path = os.path.join('Tool', 'tools', f"{name}.py")
    if not os.path.exists(path):
        raise HTTPException(status_code=404, detail="Tool not found")
    
    write_tool_file(spec)
    return {"message": "Tool updated", "name": name}

@app.delete("/tool/{name}")
async def delete_tool(name: str):
    """刪除工具"""
    remove_tool_file(name)
    return {"message": "Tool deleted", "name": name}

@app.delete("/agent/{agent_id}")
async def delete_agent(agent_id: str):
    path = os.path.join("agents", f"{agent_id}.json")
    if not os.path.exists(path):
        raise HTTPException(status_code=404, detail="Agent not found")
    
    # 刪除工具
    cfg = load_agent_config(agent_id)
    for name in cfg.get('tools', []):
        remove_tool_file(name)
    
    # 刪除配置
    os.remove(path)
    return {"message": "Agent deleted", "agent_id": agent_id}

if __name__ == '__main__':
    import uvicorn
    uvicorn.run(app,port=8888,host="0.0.0.0")
