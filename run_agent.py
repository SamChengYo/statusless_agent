import os
import json
from LLM import get_llm
from Tool import TOOL_FUNCTIONS
from Tool.formatter import generate_tool_schema
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
from typing import List, Dict, Optional
from fastapi.responses import StreamingResponse



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
    api_key: str
    llm_config: LLMConfig
    user_query: str
    streaming: bool = False
    system_prompt: Optional[str] = "你是一個熱心助人的幫手。"
    history: List[Dict] = []


app = FastAPI()

@app.post("/chat")
async def chat(request: QueryRequest):
    try:
        cfg = load_agent_config(request.agent_id)

        # 覆蓋 LLM config 中的敏感資料
        cfg['llm_config'].update({
            'provider': request.llm_config.provider,
            'model_name': request.llm_config.model_name,
            'api_base': request.llm_config.api_base,
            'temperature': request.llm_config.temperature,
            'max_tokens': request.llm_config.max_tokens,
        })

        llm = get_llm(
            provider=cfg['llm_config']['provider'],
            model_name=cfg['llm_config']['model_name'],
            api_key=request.api_key,
            api_base=cfg['llm_config'].get('api_base'),
            temperature=cfg['llm_config']['temperature'],
            max_tokens=cfg['llm_config']['max_tokens']
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






if __name__ == '__main__':
    import uvicorn
    uvicorn.run(app,port=8000,host="0.0.0.0")
