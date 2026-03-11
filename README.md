# 智扫通机器人智能客服系统

一个基于 LangChain + LangGraph 构建的智能客服 Agent，专门为扫地机器人和扫描一体机器人提供专业问答服务和使用报告生成功能。

## 功能特性

- **ReAct Agent** - 实现「思考→行动→观察→再思考」推理循环
- **RAG 知识检索** - 基于 ChromaDB 向量库的专业知识问答
- **MCP 协议集成** - 支持12306车票等外部工具
- **动态提示词切换** - 根据场景自动切换系统提示词
- **个性化报告生成** - 支持用户使用记录查询与报告输出
- **流式输出** - 实时响应，提升用户体验


## 项目结构

```
Agent/
├── app.py                    # Streamlit 应用入口
├── agent/
│   ├── react_agent.py        # ReAct Agent 核心实现
│   └── tools/
│       ├── agent_tools.py    # 自定义工具集
│       └── middleware.py     # 中间件（监控、动态提示词）
├── rag/
│   ├── rag_service.py        # RAG 检索服务
│   └── vector_store.py       # 向量存储服务
├── model/
│   └── factory.py            # 模型工厂
├── config/                   # 配置文件目录
│   ├── agent.yml
│   ├── mcp.yml
│   ├── rag.yml
│   └── prompts.yml
├── prompts/                  # 提示词模板
├── data/                     # 知识库数据
└── chroma_db/               # 向量数据库存储
```

## 快速开始

### 1. 环境要求

- Python 3.10+
- Node.js 18+ (用于 MCP 工具)

### 2. 安装依赖

```bash
pip install -r requirements.txt
```

### 3. 配置 API Key

在 `config/rag.yml` 中配置通义千问 API Key：

```yaml
chat_model_name: qwen-plus
embedding_model_name: text-embedding-v4
```

设置环境变量：
```bash
export DASHSCOPE_API_KEY="your_api_key"
```


### 4. 启动应用

```bash
streamlit run app.py
```

## 工具说明

| 工具名称 | 功能描述 |
|---------|---------|
| `rag_summarize` | 从向量库检索扫地机器人专业知识 |
| `get_user_id` | 获取当前用户 ID |
| `get_current_time` | 获取系统当前日期 |
| `fetch_external_data` | 获取用户使用记录数据 |
| `fill_context_for_report` | 触发报告生成上下文注入 |
| `maps_weather` | 高德天气查询 (MCP) |



## License

MIT License
