import uuid
import json
import os
from typing import Dict, List, Optional, Any
from .models import AgentConfig, AgentResponse, Tool, ModelConfig


class AgentManager:
    """Agent管理器類"""
    
    def __init__(self, storage_path: str = "agents"):
        """
        初始化Agent管理器
        
        Args:
            storage_path: Agent配置存儲路徑
        """
        self.storage_path = storage_path
        # 確保存儲目錄存在
        os.makedirs(os.path.join(os.path.dirname(__file__), "..", storage_path), exist_ok=True)
    
    def create_agent(self, config: AgentConfig) -> AgentResponse:
        """
        創建新的Agent
        
        Args:
            config: Agent配置
            
        Returns:
            AgentResponse: 創建結果
        """
        # 生成唯一ID
        agent_id = str(uuid.uuid4())
        
        # 構建Agent數據
        agent_data = config.dict()
        agent_data["agent_id"] = agent_id
        
        # 保存Agent配置
        self._save_agent_config(agent_id, agent_data)
        
        return AgentResponse(
            agent_id=agent_id,
            agent_name=config.agent_name,
            status="success",
            message="Agent創建成功"
        )
    
    def get_agent(self, agent_id: str) -> Optional[Dict[str, Any]]:
        """
        獲取Agent配置
        
        Args:
            agent_id: Agent ID
            
        Returns:
            Optional[Dict[str, Any]]: Agent配置，如果不存在則返回None
        """
        config_path = self._get_agent_config_path(agent_id)
        if not os.path.exists(config_path):
            return None
        
        with open(config_path, "r", encoding="utf-8") as f:
            return json.load(f)
    
    def list_agents(self) -> List[Dict[str, Any]]:
        """
        列出所有Agent
        
        Returns:
            List[Dict[str, Any]]: Agent列表
        """
        agents = []
        storage_dir = os.path.join(os.path.dirname(__file__), "..", self.storage_path)
        
        if not os.path.exists(storage_dir):
            return agents
        
        for filename in os.listdir(storage_dir):
            if filename.endswith(".json"):
                agent_id = filename.replace(".json", "")
                agent_config = self.get_agent(agent_id)
                if agent_config:
                    agents.append({
                        "agent_id": agent_id,
                        "agent_name": agent_config.get("agent_name", ""),
                        "agent_description": agent_config.get("agent_description", ""),
                        "is_public": agent_config.get("is_public", False)
                    })
        
        return agents
    
    def update_agent(self, agent_id: str, config: AgentConfig) -> AgentResponse:
        """
        更新Agent配置
        
        Args:
            agent_id: Agent ID
            config: 新的Agent配置
            
        Returns:
            AgentResponse: 更新結果
        """
        if not self.get_agent(agent_id):
            return AgentResponse(
                agent_id=agent_id,
                agent_name=config.agent_name,
                status="error",
                message="Agent不存在"
            )
        
        # 更新Agent數據
        agent_data = config.dict()
        agent_data["agent_id"] = agent_id
        
        # 保存更新後的配置
        self._save_agent_config(agent_id, agent_data)
        
        return AgentResponse(
            agent_id=agent_id,
            agent_name=config.agent_name,
            status="success",
            message="Agent更新成功"
        )
    
    def delete_agent(self, agent_id: str) -> AgentResponse:
        """
        刪除Agent
        
        Args:
            agent_id: Agent ID
            
        Returns:
            AgentResponse: 刪除結果
        """
        config_path = self._get_agent_config_path(agent_id)
        if not os.path.exists(config_path):
            return AgentResponse(
                agent_id=agent_id,
                agent_name="",
                status="error",
                message="Agent不存在"
            )
        
        # 刪除配置文件
        os.remove(config_path)
        
        return AgentResponse(
            agent_id=agent_id,
            agent_name="",
            status="success",
            message="Agent刪除成功"
        )
    
    def _get_agent_config_path(self, agent_id: str) -> str:
        """
        獲取Agent配置文件路徑
        
        Args:
            agent_id: Agent ID
            
        Returns:
            str: 配置文件路徑
        """
        return os.path.join(os.path.dirname(__file__), "..", self.storage_path, f"{agent_id}.json")
    
    def _save_agent_config(self, agent_id: str, config_data: Dict[str, Any]) -> None:
        """
        保存Agent配置
        
        Args:
            agent_id: Agent ID
            config_data: 配置數據
        """
        config_path = self._get_agent_config_path(agent_id)
        with open(config_path, "w", encoding="utf-8") as f:
            json.dump(config_data, f, ensure_ascii=False, indent=2)