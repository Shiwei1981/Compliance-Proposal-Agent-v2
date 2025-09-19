import asyncio
from typing import Optional
from contextlib import AsyncExitStack
import os
import json
from typing import List
from openai import AzureOpenAI
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
from StaticVar import api_key, endpoint, api_version, model_name, model_name_emb, model_name_reasoning, model_name_reasoning_mini
from StaticVar import cal_toten
from langchain_core.messages import AIMessage, HumanMessage, SystemMessage
from StaticVar import get_para

max_tool_calls_allowed = 20  # 每轮对话中允许最多调用 20 次工具

class MCPClient:
    def __init__(self):
        # 初始化 session 和客户端对象
        # self.session: Optional[ClientSession] = None
        # 这里改成 session 的数组        
        self.sessions = {}
        # 新增字典来存储子进程信息
        self.processes = {}  
        # 初始化一个字典来存储 tool 到 session 的映射  
        self.tool_to_session_map = {}  
        self.exit_stack = AsyncExitStack()
        # 由于涉及到线程并发，放一个锁
        self.lock_status = "release"

        # 初始化 OpenAI 客户端
        self.LLM = AzureOpenAI(
            api_key=api_key,
            azure_endpoint=endpoint,
            api_version=api_version)

    #集成3个MCP Server，需要保持3个 session，在这里做一个 connect 方法，一会儿通过不同参数，创建不同 session
    async def connect_to_server(self, server_script_path: str, mcp_server_name: str, env: dict = {}):
        """连接到 MCP 服务器

        参数:
            server_script_path: 服务器脚本路径 (.py 或 .js 文件)
        """
        is_python = server_script_path.endswith(".py")
        is_js = server_script_path.endswith(".js")
        if not (is_python or is_js):
            raise ValueError("服务器脚本必须是 .py 或 .js 文件")      

        command = "python" if is_python else "node"
        server_params = StdioServerParameters(
            command=command, args=[server_script_path], env=env
        )

        """
        process = await asyncio.create_subprocess_exec(  
            command,  
            server_script_path,  
            stdin=asyncio.subprocess.PIPE,  
            stdout=asyncio.subprocess.PIPE,  
            stderr=asyncio.subprocess.PIPE,  
            env=env  
        )  
        self.processes[mcp_server_name] = process  # 存储子进程引用
        # 创建会话  
        stdio = process.stdout  
        write = process.stdin  
        self.sessions[mcp_server_name] = await self.exit_stack.enter_async_context(  
            ClientSession(stdio, write)  
        ) 
        """
        # 启动子进程并建立标准输入输出通信
        stdio_transport = await self.exit_stack.enter_async_context(
            stdio_client(server_params)
        )
        self.processes[mcp_server_name] = stdio_transport
        stdio, write = self.processes[mcp_server_name]
        self.sessions[mcp_server_name] = await self.exit_stack.enter_async_context(
            ClientSession(stdio, write)
        )
                
        # 初始化客户端 session
        await self.sessions[mcp_server_name].initialize()

        # 列出可用工具
        response = await self.sessions[mcp_server_name].list_tools()
        tools = response.tools
        print(
            "\n成功连接到服务器，检测到的工具：",
            [[tool.name, tool.description, tool.inputSchema] for tool in tools],
        )

    async def process_query(self, query: str) -> list[dict]:
        """处理用户查询，支持多轮工具调用"""
        system_prompt = get_para("question_analyze_system_prompt")
        messages = [{"role": "user", "content": query}]

        # 获取当前可用工具
        # response = await self.session.list_tools()
        # 获取多个 MCP client 的 所有可用工具
        all_tools = []
        for key in self.sessions:  
            print(f"Session Name: {key}")  
            response = await self.sessions[key].list_tools()
            
            for tool in response.tools:  
                # 创建字典  
                tool_dict = {  
                    "type": "function",  
                    "function": {  
                        "name": tool.name,  
                        "description": tool.description,  
                        "parameters": getattr(tool, "inputSchema", {}),  
                    }  
                }  
                # 将字典添加到列表中  
                all_tools.append(tool_dict)  
                self.tool_to_session_map[tool.name] = key
            """
            available_tools = [
                {
                    "type": "function",
                    "function": {
                        "name": tool.name,
                        "description": tool.description,
                        "parameters": getattr(tool, "inputSchema", {}),
                        "mcp_server_name": key
                    },
                }
                for tool in response.tools
            ]
            all_tools = all_tools + available_tools
            """

        # 开始对话循环
        current_tool_calls_count = 0
        while True:  # 不限制总调用次数，但会受到 max_tool_calls_allowed 控制
            
            model_response = self.LLM.chat.completions.create(
                model=model_name_reasoning,
                messages=messages,
                tools=all_tools,
                tool_choice="auto",
                )
            
            prompt_str = "".join(m["content"] for m in messages)  
            cal_toten(model_name = model_name_reasoning, prompt_str=prompt_str, output = model_response.choices[0].message.content)
            
            print("\n 向助手发送消息:", query)
            assistant_message = model_response.choices[0].message
            ##logger.debug(f"助手返回消息: {assistant_message}")
            print("\n\n 助手返回消息:", assistant_message)

            # 将助手回复加入对话消息中
            messages.append({
                "role": "assistant",
                "content": assistant_message.content or "",
                "tool_calls": getattr(assistant_message, "tool_calls", None)
            })

            # 判断是否需要调用工具
            if not hasattr(assistant_message, "tool_calls") or not assistant_message.tool_calls or max_tool_calls_allowed <= current_tool_calls_count:
                # 无需调用工具，直接返回最终回复
                return messages

            # 当前轮处理所有工具调用
            # 这里注意，官方 demo 中，tool name 和 mcp server name 即 session name 是缺乏对应关系的
            for tool_call in assistant_message.tool_calls:
                try:
                    tool_name = tool_call.function.name
                    tool_args = json.loads(tool_call.function.arguments)
                    
                    ##logger.debug(f"执行工具: {tool_name}，参数: {tool_args}")
                    print("\n 执行工具:", tool_name, "参数:", tool_args)
                    # 在这里使用了前面构造的 tool 与 MCP Server  即 Tool 的对应表
                    result = await self.sessions[self.tool_to_session_map[tool_name]].call_tool(tool_name, tool_args)
                    ##logger.debug(f"工具返回结果: {result}")
                    print("\n 工具返回结果:", result)

                    # 保证结果是字符串
                    if isinstance(result, bytes):
                        result = result.decode('utf-8', errors='replace')
                    elif not isinstance(result, str):
                        result = str(result)

                    # 工具调用结果加入对话
                    messages.append({
                        "role": "tool",
                        "content": result,
                        "tool_call_id": tool_call.id
                    })

                except Exception as e:
                    error_msg = f"工具调用失败: {str(e)}"
                    ##logger.error(error_msg)
                    print("\n 工具调用失败:", error_msg)
                    messages.append({
                        "role": "tool",
                        "content": f"Error: {str(e)}",
                        "tool_call_id": tool_call.id
                    })
            
            current_tool_calls_count += 1
            if current_tool_calls_count >= max_tool_calls_allowed:
                ##logger.warning("工具调用次数过多，停止调用。")
                print("\n 工具调用次数过多，停止调用。")
                return messages

    async def chat_loop(self):
        """运行交互式聊天循环"""
        print("\nMCP 客户端已启动！")
        print("输入你的问题，或输入 'quit' 退出。")

        while True:
            try:
                query = input("\nQuery: ").strip()

                if query.lower() == "quit":
                    break

                response = await self.process_query(query)
                print("\n" + response)

            except Exception as e:
                ##logger.exception("聊天循环中出错")
                print(f"\n出错了: {str(e)}")

    async def cleanup(self):
        """清理资源"""
        # 不释放 MCP server 的 connection
        self.sessions.clear()
        await self.exit_stack.aclose()

async def main():
    env={
            "AZURE_OPENAI_API_KEY":api_key,
            "AZURE_OPENAI_ENDPOINT":endpoint,
            "AZURE_OPENAI_API_VERSION":api_version,
            "AZURE_OPENAI_MODEL_NAME":model_name,
            "AZURE_OPENAI_MODEL_NAME_EMB":model_name_emb         
        } 

    client = MCPClient()
    try:
        await client.connect_to_server("mcp_rag\\mcp_server_rag.py", "mcp_server_rag", env)
        await client.connect_to_server("ddg_search\\src\\index.js", "websearch-mcp", env)
        await client.connect_to_server("mcp_csv_query\\csv_query.py", "mcp_csv_query", env)
        await client.chat_loop()
    finally:
        await client.cleanup()

if __name__ == "__main__":
    import sys

    asyncio.run(main())
