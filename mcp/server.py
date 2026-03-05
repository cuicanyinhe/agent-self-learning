from fastmcp import FastMCP
from datetime import datetime

mcp = FastMCP()

#12306车票查询
my12306_mcp_serve_config = {
    "url":"https://mcp.api-inference.modelscope.net/cbef06000a1b46/mcp" ,
    "transport": "sse" ,
}
