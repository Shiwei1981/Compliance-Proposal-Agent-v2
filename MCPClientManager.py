from MCPClinet import MCPClient
from enum import Enum
import asyncio
import time
from StaticVar import api_key, endpoint, api_version, model_name, model_name_emb, model_name_reasoning, model_name_reasoning_mini
from StaticVar import cal_toten, get_para

class mcp_tools_class:  
    MCP_PDF = "disable"  
    MCP_CSV = "disable"  
    MCP_DDGWEBSEARCH = "disable"  


env={
    "AZURE_OPENAI_API_KEY":api_key,
    "AZURE_OPENAI_ENDPOINT":endpoint,
    "AZURE_OPENAI_API_VERSION":api_version,
    "AZURE_OPENAI_MODEL_NAME":model_name,
    "AZURE_OPENAI_MODEL_NAME_EMB":model_name_emb       
} 

client = MCPClient()

async def mcp_init_and_process_query(query: str, tool_list: mcp_tools_class)-> list[dict]:
    global client
    try:
        if tool_list.MCP_PDF == "enable":
            if all('mcp_server_rag' not in d for d in client.sessions):
                await client.connect_to_server("mcp_rag\\mcp_server_rag.py", "mcp_server_rag", env)
                print("mcp_server_rag init complete")
        if tool_list.MCP_DDGWEBSEARCH == "enable":
            if all('websearch-mcp' not in d for d in client.sessions):
                await client.connect_to_server("ddg_search\\src\\index.js", "websearch-mcp", env)
                print("websearch init complete")
        if tool_list.MCP_CSV == "enable":
            if all('mcp_csv_query' not in d for d in client.sessions):
                await client.connect_to_server("mcp_csv_query\\csv_query.py", "mcp_csv_query", env)
                print("mcp_csv_query init complete")
        result = await client.process_query(query)
    finally:
        await client.cleanup()
    return result

def mcp_process_query(query: str) -> list[dict]:
    return asyncio.run(client.process_query(query))
