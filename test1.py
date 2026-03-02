import os
from openai import OpenAI
from langchain.agents import create_agent

client = OpenAI(
    base_url="https://dashscope.aliyuncs.com/compatible-mode/v1",
)
completion = client.chat.completions.create(
    model="qwen3.5-plus",
    messages=[
        {'role': 'system', 'content': "你是一个回答简单的"},
        {'role': 'assistant', 'content': "好的，我是，并且话不多，你要问什么？"},
        {'role': 'user', 'content': "你是谁？"}]
)
print(completion.choices[0].message.content)