// API 基礎 URL
const API_BASE_URL = 'https://bot.agatha-ai.com/flowise/4a5636fa-3532-4c02-b6fe-4a5b900a7da3/';

// 當前 Agent ID
let currentAgentId = '';

// 檢查 API 服務器是否可用
async function checkApiServer() {
    try {
        const response = await fetch(`${API_BASE_URL}/docs`, {
            method: 'HEAD',
            timeout: 2000
        });
        return response.ok;
    } catch (error) {
        console.error('API 服務器檢查錯誤:', error);
        return false;
    }
}

// 顯示 API 服務器狀態
function showApiStatus(isAvailable) {
    const statusDiv = document.createElement('div');
    statusDiv.className = 'api-status';
    statusDiv.style.position = 'fixed';
    statusDiv.style.top = '10px';
    statusDiv.style.right = '10px';
    statusDiv.style.padding = '5px 10px';
    statusDiv.style.borderRadius = '4px';
    statusDiv.style.fontSize = '12px';
    
    if (isAvailable) {
        statusDiv.style.backgroundColor = '#d4edda';
        statusDiv.style.color = '#155724';
        statusDiv.textContent = 'API 服務器已連接';
    } else {
        statusDiv.style.backgroundColor = '#f8d7da';
        statusDiv.style.color = '#721c24';
        statusDiv.textContent = 'API 服務器未連接';
    }
    
    document.body.appendChild(statusDiv);
}

// DOM 元素載入完成後執行
document.addEventListener('DOMContentLoaded', async () => {
    // 檢查 API 服務器
    const isApiAvailable = await checkApiServer();
    showApiStatus(isApiAvailable);
    
    if (!isApiAvailable) {
        alert('警告：API 服務器未連接。請確保 main.py 已啟動，並運行在 8888 端口。');
    }
    // 標籤頁切換功能
    const tabBtns = document.querySelectorAll('.tab-btn');
    const tabPanes = document.querySelectorAll('.tab-pane');
    
    tabBtns.forEach(btn => {
        btn.addEventListener('click', () => {
            const tabId = btn.getAttribute('data-tab');
            
            // 移除所有標籤頁的 active 類
            tabBtns.forEach(b => b.classList.remove('active'));
            tabPanes.forEach(p => p.classList.remove('active'));
            
            // 為當前標籤頁添加 active 類
            btn.classList.add('active');
            document.getElementById(tabId).classList.add('active');
        });
    });
    
    // 工具類型切換功能
    const toolType = document.getElementById('tool-type');
    const apiOnlyFields = document.querySelectorAll('.api-only');
    
    toolType.addEventListener('change', () => {
        if (toolType.value === 'api') {
            apiOnlyFields.forEach(field => field.style.display = 'block');
        } else {
            apiOnlyFields.forEach(field => field.style.display = 'none');
        }
    });
    
    // 溫度滑塊值顯示
    const tempSlider = document.getElementById('chat-temperature');
    const tempValue = document.getElementById('temperature-value');
    
    tempSlider.addEventListener('input', () => {
        tempValue.textContent = tempSlider.value;
    });
    
    // 表單提交處理
    setupAgentForm();
    setupToolForm();
    setupChatForm();
});

// 設置 Agent 表單
function setupAgentForm() {
    const agentForm = document.getElementById('agent-form');
    const agentResult = document.getElementById('agent-result');
    
    agentForm.addEventListener('submit', async (e) => {
        e.preventDefault();
        
        // 獲取表單數據
        const name = document.getElementById('agent-name').value;
        const description = document.getElementById('agent-description').value;
        const isPublic = document.getElementById('agent-public').checked;
        const systemPrompt = document.getElementById('agent-prompt').value;
        const knowledgeBase = document.getElementById('agent-kb').value;
        const skipEncryption = document.getElementById('skip-encryption').checked;
        const password = skipEncryption ? "" : document.getElementById('agent-password').value;
        
        // 獲取選中的工具
        const tools = [];
        document.querySelectorAll('#tools-list input[type="checkbox"]:checked').forEach(checkbox => {
            tools.push({
                type: 'select',
                name: checkbox.id.replace('tool-', ''),
                content: "",  // 即使是 select 類型，也需要提供空的 content 字段
                description: null  // 添加 description 字段，設為 null
            });
        });
        
        // 獲取 API 密鑰
        const apiKeys = {
            openai: document.getElementById('api-openai').value,
            anthropic: document.getElementById('api-anthropic').value,
            google: document.getElementById('api-google').value,
            huggingface: document.getElementById('api-huggingface').value || "",
            grok: document.getElementById('api-grok').value || "",
            groq: document.getElementById('api-groq').value || ""
        };
        
        // 構建請求數據
        const data = {
            name,
            description,
            is_public: isPublic,
            system_prompt: systemPrompt,
            tools,
            knowledge_base: knowledgeBase,
            api_keys: apiKeys,
            password
        };
        
        try {
            // 顯示加載中
            agentResult.innerHTML = '<div>處理中... <div class="loading"></div></div>';
            
            console.log('發送的數據:', JSON.stringify(data, null, 2));
            
            // 發送請求
            const response = await fetch(`${API_BASE_URL}/agent`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(data),
                mode: 'no-cors' // 嘗試繞過 CORS 限制
            });
            
            console.log('API 響應狀態:', response.status, response.type);
            
            // 使用 no-cors 模式時，response.type 將是 'opaque'，無法讀取內容
            if (response.type === 'opaque') {
                // 由於無法讀取響應內容，我們假設請求成功
                console.log('使用 no-cors 模式，無法讀取響應內容，假設請求成功');
                
                // 生成一個臨時 ID
                const tempId = 'TEMP-' + Math.random().toString(36).substring(2, 8).toUpperCase();
                
                // 顯示成功訊息
                agentResult.innerHTML = `
                    <div>
                        <h3>Agent 可能已創建成功！</h3>
                        <p>由於 CORS 限制，無法確認實際結果。</p>
                        <p>臨時 ID: <strong>${tempId}</strong></p>
                        <p>請檢查後端控制台以確認是否成功。</p>
                        <p>如需解決 CORS 問題，請在 main.py 中添加 CORS 支持：</p>
                        <pre style="background: #f8f8f8; padding: 10px; overflow: auto;">
from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 允許所有來源，生產環境中應限制
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
</pre>
                    </div>
                `;
                
                // 自動填充聊天頁面的 Agent ID
                document.getElementById('chat-agent-id').value = tempId;
                return;
            }
            
            const responseText = await response.text();
            console.log('API 響應:', responseText);
            
            let result;
            try {
                result = JSON.parse(responseText);
            } catch (e) {
                console.error('解析 JSON 失敗:', e);
                throw new Error(`API 返回了無效的 JSON: ${responseText}`);
            }
            
            if (response.ok) {
                // 保存 Agent ID
                currentAgentId = result.agent_id;
                
                // 顯示成功訊息
                agentResult.innerHTML = `
                    <div>
                        <h3>Agent 創建成功！</h3>
                        <p>Agent ID: <strong>${result.agent_id}</strong></p>
                        <p>請保存此 ID 以便後續使用。</p>
                    </div>
                `;
                
                // 自動填充聊天頁面的 Agent ID
                document.getElementById('chat-agent-id').value = result.agent_id;
            } else {
                // 顯示錯誤訊息
                agentResult.innerHTML = `
                    <div style="color: red;">
                        <h3>錯誤</h3>
                        <p>${result.detail || '創建 Agent 失敗'}</p>
                        <pre style="background: #f8f8f8; padding: 10px; overflow: auto; max-height: 200px; font-size: 12px;">${JSON.stringify(result, null, 2)}</pre>
                    </div>
                `;
            }
        } catch (error) {
            console.error('創建 Agent 錯誤:', error);
            // 顯示錯誤訊息
            agentResult.innerHTML = `
                <div style="color: red;">
                    <h3>錯誤</h3>
                    <p>${error.message || '網絡錯誤'}</p>
                    <p>請檢查控制台獲取更多信息。</p>
                    <p>可能的原因：</p>
                    <ul>
                        <li>API 服務器未運行（確保 main.py 已啟動）</li>
                        <li>API 端點不正確（當前設置為 ${API_BASE_URL}）</li>
                        <li>請求格式不正確</li>
                        <li>缺少必要的目錄結構（如 agents、Tool/tools 等）</li>
                    </ul>
                </div>
            `;
        }
    });
}

// 設置工具表單
function setupToolForm() {
    const toolForm = document.getElementById('tool-form');
    const toolResult = document.getElementById('tool-result');
    
    toolForm.addEventListener('submit', async (e) => {
        e.preventDefault();
        
        // 獲取表單數據
        const type = document.getElementById('tool-type').value;
        const name = document.getElementById('tool-name').value;
        const content = document.getElementById('tool-content').value;
        const description = document.getElementById('tool-description').value;
        
        // 構建請求數據
        const data = {
            type,
            name,
            content,
            description: type === 'api' ? description : ''
        };
        
        try {
            // 顯示加載中
            toolResult.innerHTML = '<div>處理中... <div class="loading"></div></div>';
            
            // 發送請求
            const response = await fetch(`${API_BASE_URL}/tool`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(data),
                mode: 'no-cors' // 嘗試繞過 CORS 限制
            });
            
            console.log('API 響應狀態:', response.status, response.type);
            
            // 使用 no-cors 模式時，response.type 將是 'opaque'，無法讀取內容
            if (response.type === 'opaque') {
                // 由於無法讀取響應內容，我們假設請求成功
                console.log('使用 no-cors 模式，無法讀取響應內容，假設請求成功');
                
                // 顯示成功訊息
                toolResult.innerHTML = `
                    <div>
                        <h3>工具可能已創建成功！</h3>
                        <p>由於 CORS 限制，無法確認實際結果。</p>
                        <p>工具名稱: <strong>${name}</strong></p>
                        <p>請檢查後端控制台以確認是否成功。</p>
                    </div>
                `;
                
                // 添加到工具列表
                const toolsList = document.getElementById('tools-list');
                const toolItem = document.createElement('div');
                toolItem.className = 'tool-item';
                toolItem.innerHTML = `
                    <input type="checkbox" id="tool-${name}" checked>
                    <label for="tool-${name}">${name}</label>
                `;
                toolsList.appendChild(toolItem);
                return;
            }
            
            const result = await response.json();
            
            if (response.ok) {
                // 顯示成功訊息
                toolResult.innerHTML = `
                    <div>
                        <h3>工具創建成功！</h3>
                        <p>工具名稱: <strong>${result.name}</strong></p>
                    </div>
                `;
                
                // 添加到工具列表
                const toolsList = document.getElementById('tools-list');
                const toolItem = document.createElement('div');
                toolItem.className = 'tool-item';
                toolItem.innerHTML = `
                    <input type="checkbox" id="tool-${name}" checked>
                    <label for="tool-${name}">${name}</label>
                `;
                toolsList.appendChild(toolItem);
            } else {
                // 顯示錯誤訊息
                toolResult.innerHTML = `
                    <div style="color: red;">
                        <h3>錯誤</h3>
                        <p>${result.detail || '創建工具失敗'}</p>
                    </div>
                `;
            }
        } catch (error) {
            // 顯示錯誤訊息
            toolResult.innerHTML = `
                <div style="color: red;">
                    <h3>錯誤</h3>
                    <p>${error.message || '網絡錯誤'}</p>
                </div>
            `;
        }
    });
}

// 設置聊天功能
function setupChatForm() {
    const chatMessages = document.getElementById('chat-messages');
    const userInput = document.getElementById('user-input');
    const sendBtn = document.getElementById('send-btn');
    
    // 聊天歷史
    const chatHistory = [];
    
    // 發送按鈕點擊事件
    sendBtn.addEventListener('click', () => {
        const message = userInput.value.trim();
        if (message) {
            sendMessage(message);
            userInput.value = '';
        }
    });
    
    // 按 Enter 鍵發送訊息
    userInput.addEventListener('keypress', (e) => {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            sendBtn.click();
        }
    });
    
    // 發送訊息函數
    async function sendMessage(message) {
        // 顯示用戶訊息
        appendMessage('user', message);
        
        // 獲取聊天配置
        const agentId = document.getElementById('chat-agent-id').value;
        const model = document.getElementById('chat-model').value;
        const provider = document.getElementById('chat-provider').value;
        const temperature = parseFloat(document.getElementById('chat-temperature').value);
        const maxTokens = parseInt(document.getElementById('chat-max-tokens').value);
        const streaming = document.getElementById('chat-streaming').checked;
        const password = document.getElementById('chat-password').value;
        
        // 構建請求數據
        const data = {
            agent_id: agentId,
            llm_config: {
                model_name: model,
                provider: provider,
                temperature: temperature,
                max_tokens: maxTokens
            },
            user_query: message,
            streaming: streaming,
            history: chatHistory,
            password: password
        };
        
        try {
            // 創建 bot 訊息容器
            const botMessageContainer = document.createElement('div');
            botMessageContainer.className = 'message bot-message';
            chatMessages.appendChild(botMessageContainer);
            
            // 滾動到底部
            chatMessages.scrollTop = chatMessages.scrollHeight;
            
            if (streaming) {
                // 流式響應處理
                const response = await fetch(`${API_BASE_URL}/chat`, {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify(data),
                    mode: 'no-cors' // 嘗試繞過 CORS 限制
                });
                
                console.log('API 響應狀態:', response.status, response.type);
                
                // 使用 no-cors 模式時，response.type 將是 'opaque'，無法讀取內容
                if (response.type === 'opaque') {
                    // 由於無法讀取響應內容，我們顯示一個提示訊息
                    console.log('使用 no-cors 模式，無法讀取流式響應內容');
                    
                    const simulatedMessage = "由於 CORS 限制，無法獲取實際響應。這是一個模擬的回應。\n\n" +
                        "要解決 CORS 問題，請在 main.py 中添加 CORS 支持：\n\n" +
                        "```python\n" +
                        "from fastapi.middleware.cors import CORSMiddleware\n\n" +
                        "app.add_middleware(\n" +
                        "    CORSMiddleware,\n" +
                        "    allow_origins=[\"*\"],  # 允許所有來源，生產環境中應限制\n" +
                        "    allow_credentials=True,\n" +
                        "    allow_methods=[\"*\"],\n" +
                        "    allow_headers=[\"*\"],\n" +
                        ")\n" +
                        "```";
                    
                    botMessageContainer.innerHTML = formatMessage(simulatedMessage);
                    
                    // 更新聊天歷史
                    chatHistory.push({ role: 'user', content: message });
                    chatHistory.push({ role: 'assistant', content: simulatedMessage });
                    
                    return;
                }
                
                try {
                    const reader = response.body.getReader();
                    const decoder = new TextDecoder();
                    let botMessage = '';
                    
                    while (true) {
                        const { value, done } = await reader.read();
                        if (done) break;
                        
                        const chunk = decoder.decode(value);
                        const lines = chunk.split('\n');
                        
                        for (const line of lines) {
                            if (line.startsWith('data: ')) {
                                const content = line.substring(6);
                                if (content === 'done') break;
                                botMessage += content;
                                botMessageContainer.innerHTML = formatMessage(botMessage);
                                
                                // 滾動到底部
                                chatMessages.scrollTop = chatMessages.scrollHeight;
                            }
                        }
                    }
                    
                    // 更新聊天歷史
                    chatHistory.push({ role: 'user', content: message });
                    chatHistory.push({ role: 'assistant', content: botMessage });
                } catch (error) {
                    console.error('流式讀取錯誤:', error);
                    botMessageContainer.innerHTML = `<div style="color: red;">流式讀取錯誤: ${error.message}</div>`;
                }
            } else {
                // 非流式響應處理
                botMessageContainer.innerHTML = '思考中... <div class="loading"></div>';
                
                const response = await fetch(`${API_BASE_URL}/chat`, {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify(data),
                    mode: 'no-cors' // 嘗試繞過 CORS 限制
                });
                
                console.log('API 響應狀態:', response.status, response.type);
                
                // 使用 no-cors 模式時，response.type 將是 'opaque'，無法讀取內容
                if (response.type === 'opaque') {
                    // 由於無法讀取響應內容，我們顯示一個提示訊息
                    console.log('使用 no-cors 模式，無法讀取非流式響應內容');
                    
                    const simulatedMessage = "由於 CORS 限制，無法獲取實際響應。這是一個模擬的回應。\n\n" +
                        "要解決 CORS 問題，請在 main.py 中添加 CORS 支持：\n\n" +
                        "```python\n" +
                        "from fastapi.middleware.cors import CORSMiddleware\n\n" +
                        "app.add_middleware(\n" +
                        "    CORSMiddleware,\n" +
                        "    allow_origins=[\"*\"],  # 允許所有來源，生產環境中應限制\n" +
                        "    allow_credentials=True,\n" +
                        "    allow_methods=[\"*\"],\n" +
                        "    allow_headers=[\"*\"],\n" +
                        ")\n" +
                        "```";
                    
                    botMessageContainer.innerHTML = formatMessage(simulatedMessage);
                    
                    // 更新聊天歷史
                    chatHistory.push({ role: 'user', content: message });
                    chatHistory.push({ role: 'assistant', content: simulatedMessage });
                    
                    return;
                }
                
                try {
                    const result = await response.json();
                    
                    if (response.ok) {
                        const botMessage = result.response;
                        botMessageContainer.innerHTML = formatMessage(botMessage);
                        
                        // 更新聊天歷史
                        chatHistory.push({ role: 'user', content: message });
                        chatHistory.push({ role: 'assistant', content: botMessage });
                    } else {
                        botMessageContainer.innerHTML = `
                            <div style="color: red;">
                                <h3>錯誤</h3>
                                <p>${result.detail || '聊天請求失敗'}</p>
                            </div>
                        `;
                    }
                } catch (error) {
                    console.error('解析 JSON 錯誤:', error);
                    botMessageContainer.innerHTML = `<div style="color: red;">解析響應錯誤: ${error.message}</div>`;
                }
            }
            
            // 滾動到底部
            chatMessages.scrollTop = chatMessages.scrollHeight;
        } catch (error) {
            // 顯示錯誤訊息
            appendMessage('error', `錯誤: ${error.message || '網絡錯誤'}`);
        }
    }
    
    // 添加訊息到聊天區域
    function appendMessage(role, content) {
        const messageDiv = document.createElement('div');
        messageDiv.className = `message ${role}-message`;
        
        if (role === 'user') {
            messageDiv.textContent = content;
        } else if (role === 'error') {
            messageDiv.innerHTML = `<div style="color: red;">${content}</div>`;
        } else {
            messageDiv.innerHTML = formatMessage(content);
        }
        
        chatMessages.appendChild(messageDiv);
        chatMessages.scrollTop = chatMessages.scrollHeight;
    }
    
    // 格式化訊息（處理工具調用等）
    function formatMessage(message) {
        // 簡單的 Markdown 格式支援
        let formatted = message
            .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
            .replace(/\*(.*?)\*/g, '<em>$1</em>')
            .replace(/```([\s\S]*?)```/g, '<pre><code>$1</code></pre>')
            .replace(/`(.*?)`/g, '<code>$1</code>')
            .replace(/\n/g, '<br>');
        
        // 檢測工具調用格式
        const toolCallRegex = /工具調用: (.*?)\n參數: ([\s\S]*?)(?:\n結果: ([\s\S]*?))?(?:\n|$)/g;
        formatted = formatted.replace(toolCallRegex, (match, tool, params, result) => {
            let html = `<div class="tool-call">
                <strong>工具調用:</strong> ${tool}<br>
                <strong>參數:</strong> <pre>${params}</pre>
            `;
            
            if (result) {
                html += `<div class="tool-result">
                    <strong>結果:</strong> <pre>${result}</pre>
                </div>`;
            }
            
            html += '</div>';
            return html;
        });
        
        return formatted;
    }
}