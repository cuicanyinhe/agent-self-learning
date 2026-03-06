from langchain.agents import create_agent
from langchain_core.language_models import BaseChatModel
from langchain_core.tools import BaseTool
from langchain_mcp_adapters.client import MultiServerMCPClient

from model.factory import chat_model
from utils.prompts_loader import load_system_prompts
from agent.tools.agent_tools import *
from agent.tools.middleware import monitor_tool, log_before_model, report_prompt_switch
import asyncio
from typing import List, Optional
from utils.config_handler import mcp_conf
from utils.logger_handler import logger

class ReactAgent:
    def __init__(self):
        self.agent = create_agent(
            model=chat_model,
            system_prompt=load_system_prompts(),
            tools=[rag_summarize, get_weather, get_user_location, get_user_id,
                   get_current_month, fetch_external_data, fill_context_for_report],
            middleware=[monitor_tool, log_before_model, report_prompt_switch],
        )

    def execute_stream(self, query: str):
        input_dict = {
            "messages": [
                {"role": "user", "content": query},
            ]
        }


        for chunk in self.agent.stream(input_dict, stream_mode="values", context={"report": False}):
            latest_message = chunk["messages"][-1]
            if latest_message.content:
                yield latest_message.content.strip() + "\n"

if __name__ == '__main__':
    agent = ReactAgent()

    for chunk in agent.execute_stream("为我生成我的使用报告"):
        print(chunk, end="", flush=True)

'''
class ReactAgent:
    
    def __init__(self, chat_model: Optional[BaseChatModel] = None):
        """
        初始化 React Agent
        
        Args:
            chat_model: 可选的聊天模型，如果不提供则使用默认工厂创建
        """
        self.chat_model = chat_model or ChatModelFactory().generator()
        self.custom_tools: List[BaseTool] = []
        self.mcp_client: Optional[MultiServerMCPClient] = None
        self.agent = None
        self._tools_loaded = False #判断工具是否调用成功
        
    def _get_custom_tools(self) -> List[BaseTool]:
        """获取自定义工具（同步方法）"""
        from custom_tools import (  # 导入你的工具
            rag_summarize, get_weather, get_user_location, 
            get_user_id, get_current_month, fetch_external_data, 
            fill_context_for_report
        )
        
        self.custom_tools = [
            rag_summarize, 
            get_weather, 
            get_user_location,
            get_user_id, 
            get_current_month, 
            fetch_external_data, 
            fill_context_for_report
        ]
        
        logger.info(f"✅ 加载了 {len(self.custom_tools)} 个自定义工具")
        return self.custom_tools
    
    async def setup_mcp_connections(self, mcp_conf: dict) -> List[BaseTool]:
        """
        设置 MCP 连接并获取工具（异步方法）
        
        Args:
            mcp_conf: MCP 服务器配置字典
            
        Returns:
            MCP 工具列表
        """
        try:
            # 创建 MCP 客户端
            self.mcp_client = MultiServerMCPClient(mcp_conf)
            
            # 重要：需要进入异步上下文才能获取工具
            await self.mcp_client.__aenter__()
            
            # 获取 MCP 工具
            mcp_tools = await self.mcp_client.get_tools()
            tool_names = [t.name for t in mcp_tools]
            
            logger.info(f"🌐 从 MCP 服务器加载了 {len(mcp_tools)} 个工具: {tool_names}")
            return mcp_tools
            
        except Exception as e:
            logger.error(f"❌ MCP 连接失败: {e}")
            return []  # 返回空列表而不是崩溃
    
    async def initialize(self, mcp_conf: dict, system_prompt: str, 
                        middleware: Optional[List] = None) -> 'ReactAgent':
        """
        异步初始化 Agent（分离的初始化方法）
        
        Args:
            mcp_conf: MCP 服务器配置
            system_prompt: 系统提示词
            middleware: 中间件列表
            
        Returns:
            self（支持链式调用）
        """
        # 1. 获取自定义工具
        custom_tools = self._get_custom_tools()
        
        # 2. 获取 MCP 工具
        mcp_tools = await self.setup_mcp_connections(mcp_conf)
        
        # 3. 合并所有工具
        all_tools = custom_tools + mcp_tools
        logger.info(f"🎯 总共加载了 {len(all_tools)} 个工具 "
                   f"({len(custom_tools)}个自定义 + {len(mcp_tools)}个MCP)")
        
        # 4. 创建 Agent
        self.agent = create_react_agent(  # 使用更明确的 create_react_agent
            model=self.chat_model,
            tools=all_tools,
            prompt=system_prompt,
            # LangChain 的 agent 可能不支持直接传入 middleware
            # 如果确实需要，可能需要自定义 agent executor
        )
        
        # 如果确实需要 middleware，可以在这里包装 agent
        if middleware:
            self.agent = self._wrap_with_middleware(self.agent, middleware)
        
        self._tools_loaded = True
        return self
    
    def _wrap_with_middleware(self, agent, middleware):
        """包装 agent 以支持中间件（如果需要）"""
        # 这里可以实现自定义的中间件包装逻辑
        # 或者考虑使用 LangChain 的 callbacks 替代
        return agent
    
    async def execute_stream(self, query: str, context: Optional[Dict] = None) -> AsyncGenerator[str, None]:
        """
        流式执行查询
        
        Args:
            query: 用户查询
            context: 额外的上下文信息
            
        Yields:
            Agent 响应的文本块
        """
        if not self.agent or not self._tools_loaded:
            raise RuntimeError("Agent 未初始化，请先调用 initialize()")
        
        # 构建输入
        input_dict = {
            "messages": [
                {"role": "user", "content": query},
            ]
        }
        
        # 添加额外上下文（如果需要）
        config = {"configurable": context or {}}
        
        try:
            # 流式执行
            async for chunk in self.agent.astream(
                input_dict, 
                config=config,
                stream_mode="values"
            ):
                latest_message = chunk.get("messages", [])[-1]
                
                # 处理不同类型的消息
                if isinstance(latest_message, AIMessage) and latest_message.content:
                    # 逐块返回，避免重复的换行
                    yield latest_message.content
                    
                # 如果需要包含中间步骤，可以检查其他字段
                # if "intermediate_steps" in chunk:
                #     # 处理中间步骤...
                    
        except Exception as e:
            logger.error(f"执行出错: {e}")
            yield f"执行出错: {str(e)}"
    
    async def execute(self, query: str, context: Optional[Dict] = None) -> str:
        """
        同步执行查询（收集所有流式输出）
        
        Args:
            query: 用户查询
            context: 额外的上下文信息
            
        Returns:
            完整的响应文本
        """
        full_response = []
        async for chunk in self.execute_stream(query, context):
            full_response.append(chunk)
        return "".join(full_response)
    
    async def close(self):
        """清理资源"""
        if self.mcp_client:
            await self.mcp_client.__aexit__(None, None, None)
            logger.info("🔌 MCP 连接已关闭")
    
    async def __aenter__(self):
        """异步上下文管理器入口"""
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """异步上下文管理器出口"""
        await self.close()
'''