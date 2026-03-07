from langchain.agents import create_agent
from langchain_core.messages import AIMessage
from langchain_core.tools import BaseTool
from langchain_mcp_adapters.client import MultiServerMCPClient

from model.factory import chat_model
from utils.prompts_loader import load_system_prompts

from agent.tools.middleware import amonitor_tool, alog_before_model, areport_prompt_switch
from agent.tools.agent_tools import *
import asyncio
from typing import List, Optional, Dict, AsyncGenerator
from utils.config_handler import mcp_conf
from utils.logger_handler import logger


class ReactAgent:
    
    def __init__(self):
        """
        初始化 React Agent
        """
        self.chat_model = chat_model
        self.custom_tools: List[BaseTool] = []
        self.agent = None
        self._tools_loaded = False  #判断工具是否调用成功
        self.mcp_conf = mcp_conf
        
    def _get_custom_tools(self) -> List[BaseTool]:
        
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
    
    async def setup_mcp_connections(self) -> List[BaseTool]:
        """
        设置 MCP 连接并获取工具（异步方法）
        
        Args:
            mcp_conf: MCP 服务器配置字典
            
        Returns:
            MCP 工具列表
        """
        try:
            mcp_client = MultiServerMCPClient(self.mcp_conf)
            mcp_tools = await mcp_client.get_tools()
            tool_names = [t.name for t in mcp_tools]
            
            logger.info(f"🌐 从 MCP 服务器加载了 {len(mcp_tools)} 个工具: {tool_names}")
            return mcp_tools
            
        except Exception as e:
            logger.error(f"❌ MCP 连接失败: {e}")
            return []  # 返回空列表而不是崩溃
    
    async def initialize(self) -> 'ReactAgent':
        """
        异步初始化 Agent（分离的初始化方法）
        """
        custom_tools = self._get_custom_tools()

        mcp_tools = await self.setup_mcp_connections()
        
        # 合并所有工具
        all_tools = custom_tools + mcp_tools
        logger.info(f"🎯 总共加载了 {len(all_tools)} 个工具({len(custom_tools)}个自定义 + {len(mcp_tools)}个MCP)")
        
        #创建 Agent
        self.agent = create_agent(
            model=self.chat_model,
            tools=all_tools,
            system_prompt=load_system_prompts(),
            middleware=[amonitor_tool, alog_before_model, areport_prompt_switch],
        )
        
        self._tools_loaded = True
        return self
    
    async def execute_stream(self, query: str, context: Optional[Dict] = None) -> AsyncGenerator[str, None]:
        if not self.agent or not self._tools_loaded:
            raise RuntimeError("Agent 未初始化，请先调用 initialize()")
        
        # 构建输入
        input_dict = {
            "messages": [
                {"role": "user", "content": query},
            ]
        }

        try:
            # 流式执行
            async for chunk in self.agent.astream(
                input_dict,
                stream_mode="values",
                context={"report": False}
            ):
                latest_message = chunk["messages"][-1]
                
                # 处理不同类型的消息
                if isinstance(latest_message, AIMessage) and latest_message.content:
                    # 逐块返回，避免重复的换行
                    yield latest_message.content.strip() + "\n"

        except Exception as e:
            logger.error(f"执行出错: {e}")
    
    async def execute(self, query: str, context: Optional[Dict] = None) -> str:
        full_response = []
        async for chunk in self.execute_stream(query, context):
            full_response.append(chunk)
        return "".join(full_response)


'''if __name__ == '__main__':
    import asyncio

    async def test():
        agent = await ReactAgent().initialize()

        async for chunk in agent.execute_stream("为我生成我的使用报告"):
            print(chunk, end="", flush=True)

    asyncio.run(test())'''