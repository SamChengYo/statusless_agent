import os
import json
from LLM import get_llm
from Tool import TOOL_FUNCTIONS
from Tool.formatter import generate_tool_schema
from fastapi import FastAPI, HTTPException, Body
from pydantic import BaseModel, Field
from typing import List, Dict, Optional
from fastapi.responses import StreamingResponse
from utils.decrypt import get_key, lock_key
import secrets
import random
import string

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
    tools: List[str]
    knowledge_base: str
    api_keys: APIKeysConfig = Field(default_factory=APIKeysConfig)

app = FastAPI()

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
    agent_data = config.dict()
    agent_data["id"] = agent_id

    path = os.path.join("agents", f"{agent_id}.json")
    with open(path, "w", encoding="utf-8") as f:
        json.dump(agent_data, f, ensure_ascii=False, indent=2)

    return {"message": "Agent created", "agent_id": agent_id}

@app.put("/agent/{agent_id}")
async def update_agent(agent_id: str, config: AgentConfig):
    path = os.path.join("agents", f"{agent_id}.json")
    if not os.path.exists(path):
        raise HTTPException(status_code=404, detail="Agent not found")

    agent_data = config.dict()
    agent_data["id"] = agent_id

    with open(path, "w", encoding="utf-8") as f:
        json.dump(agent_data, f, ensure_ascii=False, indent=2)

    return {"message": "Agent updated", "agent_id": agent_id}

@app.delete("/agent/{agent_id}")
async def delete_agent(agent_id: str):
    path = os.path.join("agents", f"{agent_id}.json")
    if not os.path.exists(path):
        raise HTTPException(status_code=404, detail="Agent not found")

    os.remove(path)
    return {"message": "Agent deleted", "agent_id": agent_id}

if __name__ == '__main__':
    import uvicorn
    uvicorn.run(app,port=8000,host="0.0.0.0")