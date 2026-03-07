import time
import asyncio
import streamlit as st
from agent.react_agent import ReactAgent

# 配置页面
st.set_page_config(page_title="智扫通机器人", page_icon="🤖")
st.title("智扫通机器人智能客服")
st.divider()

# 初始化 session state
if "agent" not in st.session_state:
    st.session_state.agent = None
    st.session_state.messages = []
    st.session_state.initialized = False


# 异步初始化 agent
async def init_agent():
    agent = await ReactAgent().initialize()
    return agent


# 如果 agent 未初始化，进行初始化
if not st.session_state.initialized:
    with st.spinner("正在初始化智能客服..."):
        # 运行异步初始化
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        st.session_state.agent = loop.run_until_complete(init_agent())
        st.session_state.initialized = True
        loop.close()
    st.rerun()

# 显示历史消息
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# 处理用户输入
if prompt := st.chat_input("请输入您的问题..."):
    # 显示用户消息
    st.chat_message("user").write(prompt)
    st.session_state.messages.append({"role": "user", "content": prompt})

    # 收集响应的列表
    response_chunks = []

    # 智能客服思考中的加载状态
    with st.spinner("智能客服思考中..."):
        # 获取异步生成器
        async_gen = st.session_state.agent.execute_stream(prompt)


        # 定义捕获生成器函数
        def capture_chunks(async_generator, cache_list):
            # 创建新的事件循环
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)

            try:
                # 将异步生成器转换为同步生成器
                while True:
                    try:
                        chunk = loop.run_until_complete(async_generator.__anext__())
                        if chunk:
                            cache_list.append(chunk)
                            # 逐字符输出以实现流畅的流式效果
                            for char in chunk:
                                time.sleep(0.01)  # 控制输出速度
                                yield char
                    except StopAsyncIteration:
                        break
            finally:
                loop.close()


        # 使用 write_stream 进行流式输出
        st.chat_message("assistant").write_stream(
            capture_chunks(async_gen, response_chunks)
        )

    # 保存完整响应到历史
    if response_chunks:
        full_response = "".join(response_chunks)
        st.session_state.messages.append({"role": "assistant", "content": full_response})

    st.rerun()