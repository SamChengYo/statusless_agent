# Unicorn AI Agent 平台

Unicorn 是一個強大的 AI Agent 平台，允許使用者動態創建、管理和使用 AI 代理。該平台支援多種大型語言模型（LLM）並提供工具註冊和調用功能，使 AI 代理能夠執行各種任務。

## 功能特點

- 支援多種 LLM 提供商（OpenAI、Claude、Gemini、Ollama、HuggingFace、Grok、Groq）
- 動態工具註冊和管理
- Agent 創建和配置
- 聊天功能支援工具調用
- 流式輸出支援
- API 密鑰加密存儲

## 安裝與設置

### 前置需求

- Python 3.8+
- FastAPI
- Uvicorn
- LiteLLM

### 安裝步驟

1. 克隆此儲存庫
2. 安裝依賴：
   ```bash
   pip install -r requirements.txt
   ```
3. 啟動服務：
   ```bash
   python main.py
   ```

服務將在 `http://localhost:8888` 上運行。

## API 參考

### 聊天 API

#### POST /chat

與 AI 代理進行對話。

**請求參數：**

```json
{
  "agent_id": "ABCD-1234",
  "llm_config": {
    "model_name": "gpt-4.1",
    "provider": "openai",
    "temperature": 0.7,
    "max_tokens": 1500,
    "api_base": "https://api.openai.com/v1" // 可選
  },
  "user_query": "今天天氣如何？",
  "streaming": false,
  "system_prompt": "你是一個熱心助人的幫手。", // 可選
  "history": [], // 可選，對話歷史
  "password": "your_password" // 用於解密 API 密鑰
}
```

**響應：**

非流式模式：
```json
{
  "response": "今天天氣晴朗，溫度適宜。"
}
```

流式模式：
返回 Server-Sent Events (SSE) 格式的流式響應。

### Agent 管理 API

#### POST /agent

創建新的 AI 代理。

**請求參數：**

```json
{
  "name": "天氣助手",
  "description": "提供天氣信息的助手",
  "is_public": true,
  "system_prompt": "你是一個專業的天氣助手，提供準確的天氣信息。",
  "tools": [
    {
      "type": "function",
      "name": "get_weather",
      "content": "def get_weather(city: str, date: str = 'today') -> str:\n    \"\"\"獲取指定城市的天氣信息\"\"\"\n    return f\"{city} 在 {date} 的天氣晴朗，溫度 25 度。\""
    },
    {
      "type": "api",
      "name": "get_forecast",
      "content": "https://api.weather.com/forecast",
      "description": "獲取未來幾天的天氣預報"
    },
    {
      "type": "select",
      "name": "get_current_weather"
    }
  ],
  "knowledge_base": "",
  "api_keys": {
    "openai": "sk-...",
    "anthropic": "sk-ant-..."
  },
  "password": "your_password" // 用於加密 API 密鑰
}
```

**響應：**

```json
{
  "message": "Agent created",
  "agent_id": "ABCD-1234"
}
```

#### PUT /agent/{agent_id}

更新現有 AI 代理。

**請求參數：**

```json
{
  "name": "更新後的天氣助手",
  "description": "更新後的描述",
  "is_public": false,
  "system_prompt": "更新後的系統提示",
  "tools": ["get_weather", "get_forecast"],
  "knowledge_base": "",
  "api_keys": {
    "openai": "sk-..."
  },
  "password": "your_password"
}
```

**響應：**

```json
{
  "message": "Agent updated",
  "agent_id": "ABCD-1234"
}
```

#### DELETE /agent/{agent_id}

刪除 AI 代理。

**響應：**

```json
{
  "message": "Agent deleted",
  "agent_id": "ABCD-1234"
}
```

### 工具管理 API

#### POST /tool

創建新工具。

**請求參數：**

```json
{
  "type": "function",
  "name": "calculate_area",
  "content": "def calculate_area(length: float, width: float) -> float:\n    \"\"\"計算矩形面積\"\"\"\n    return length * width",
  "description": "計算矩形面積的函數"
}
```

**響應：**

```json
{
  "message": "Tool created",
  "name": "calculate_area"
}
```

#### PUT /tool/{name}

更新現有工具。

**請求參數：**

```json
{
  "type": "function",
  "name": "calculate_area",
  "content": "def calculate_area(length: float, width: float, height: float = None) -> float:\n    \"\"\"計算矩形或立方體面積/體積\"\"\"\n    if height is None:\n        return length * width\n    return length * width * height",
  "description": "計算矩形面積或立方體體積的函數"
}
```

**響應：**

```json
{
  "message": "Tool updated",
  "name": "calculate_area"
}
```

#### DELETE /tool/{name}

刪除工具。

**響應：**

```json
{
  "message": "Tool deleted",
  "name": "calculate_area"
}
```

## 工具開發指南

### 創建自定義工具

1. 使用 POST /tool API 創建工具，或直接在 Tool/tools/ 目錄下創建 Python 文件。
2. 使用 @register_tool() 裝飾器註冊工具函數。
3. 確保函數有清晰的類型註解和文檔字符串。

範例：

```python

def calculate_distance(x1: float, y1: float, x2: float, y2: float) -> float:
    """計算兩點之間的歐幾里得距離"""
    return ((x2 - x1) ** 2 + (y2 - y1) ** 2) ** 0.5
```

## 安全性考慮

- API 密鑰使用密碼加密存儲
- 使用 HTTPS 保護 API 通信
- 實施適當的訪問控制和身份驗證

## 使用範例

1. 創建一個 Agent
2. 註冊所需工具
3. 使用 /chat API 與 Agent 進行對話
4. Agent 可以調用註冊的工具來完成任務

## 故障排除

- 確保所有依賴都已正確安裝
- 檢查 API 密鑰是否有效
- 確保工具函數格式正確並已正確註冊

## 貢獻指南

歡迎提交 Pull Request 和 Issue 來改進此專案。

## 授權

[MIT 授權]