import logging
import json
from langchain_openai import AzureChatOpenAI
from typing import Annotated
from typing_extensions import TypedDict
from langgraph.graph.message import AnyMessage
from langchain_core.messages import AIMessage, HumanMessage, SystemMessage
from langgraph.graph import StateGraph, START, END
from typing import TypedDict, Annotated,List
from IPython.display import Image, display
from langgraph.graph.message import add_messages
from datetime import datetime
from MCPClientManager import mcp_init_and_process_query, mcp_tools_class
import asyncio
from StaticVar import api_key, endpoint, api_version, model_name, model_name_emb, model_name_reasoning, model_name_reasoning_mini
from StaticVar import cal_toten, get_para
from CommonFunc import LLM_Prompt_question_analyze
from mcp_csv_query.csv_query import get_csv_files_list, get_csv_schema


# 创建日志器  
logger = logging.getLogger('my_logger')  
logger.setLevel(logging.DEBUG)  # 设置日志器的日志级别  
  
# 创建文件处理器，并设置编码为 utf-8  
file_handler = logging.FileHandler('app.log', encoding='utf-8')  
file_handler.setLevel(logging.DEBUG)  # 设置文件处理器的日志级别  
  
# 创建格式化器  
formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')  
file_handler.setFormatter(formatter)  # 将格式化器应用到文件处理器  
  
# 将文件处理器添加到日志器  
logger.addHandler(file_handler)  

class AgentState(TypedDict):
    messages: Annotated[list[AnyMessage], add_messages]
    messages_history: Annotated[list[AnyMessage], add_messages]
    sessionid: str
    tasks_json: dict
    question: str
    number_current_task: str
    number_current_area: str
    message_area_to_area: str
    message_area_to_serial_task: str
    message_area_to_sequential_task: str
    message_area_to_parallel_task: str
    message_sequential_task_to_sequential_task: str
    direct_run: bool


#生成 task 运行提示词
def generate_task_prompt_from_JSON(node_json: dict, node_type: str, question:str) -> str:
    customer_profile=get_para("customerprofile")
    #return_str = ""
    task_json = dict()
    for key in node_json.keys():
        if not key.startswith("Metadata-"): 
            task_json[key] = node_json[key]
    task_str = json.dumps(task_json, ensure_ascii=False, indent=4)
    prompt_template_str = ''.join(get_para("taks_execution_prompt_template"))
    prompt_str = prompt_template_str.format(
        question=question, 
        customer_profile=customer_profile,
        task=task_str,
        language=get_para("language"),
        )
    return prompt_str

#生成 总结 提示词
def generate_summary_prompt_from_JSON(question:str, previouse_messages_str:str) -> str:
    taks_summary_prompt_template = get_para("taks_summary_prompt_template")
    taks_summary_prompt_template_str = ''.join(taks_summary_prompt_template)
    customer_profile=get_para("customerprofile")    
    prompt_str = taks_summary_prompt_template_str.format(
        question=question, 
        customer_profile=customer_profile,
        task_results=previouse_messages_str,
        language=get_para("language"),
        )
    return prompt_str

#根据任务内容 选择 MCP 工具
def choose_mcp_tools(node_json: dict) -> mcp_tools_class:
    tool_list = mcp_tools_class()
    if get_para("mcp_pdf") == "enable":
        if ".pdf" in node_json["对应的企业数据文件名"].lower():
            tool_list.MCP_PDF = "enable"
    if get_para("mcp_csv") == "enable":
        if ".csv" in node_json["对应的企业数据文件名"].lower():
            tool_list.MCP_CSV = "enable"
    if get_para("mcp_ddgwebsearch") == "enable":
        if node_json["需要结合的互联网数据"] != "":
            tool_list.MCP_DDGWEBSEARCH = "enable"
    if tool_list.MCP_PDF == "disable" and tool_list.MCP_CSV == "disable":
        tool_list.MCP_DDGWEBSEARCH = "enable"
    return tool_list


#生成 顺序 task 运行提示词
def generate_sequential_task_prompt_from_JSON(node_json: dict, node_type: str, question:str, sequential_tasks: str, task_number: str, input_from_previous_task: str) -> str:
    customer_profile=get_para("customerprofile")
    #return_str = ""
    task_json = dict()
    for key in node_json.keys():
        if not key.startswith("Metadata-"): 
            task_json[key] = node_json[key]
    task_str = json.dumps(task_json, ensure_ascii=False, indent=4)
    prompt_template_str = ''.join(get_para("sequential_taks_execution_prompt_template"))
    prompt_str = prompt_template_str.format(
        question=question, 
        customer_profile=customer_profile,
        task=task_str,
        task_number=task_number,
        sequential_tasks=sequential_tasks,
        input_from_previous_task=input_from_previous_task,
        language=get_para("language"),
        )
    return prompt_str

def generate_sequential_task_prompt_from_JSON_first(node_json: dict, node_type: str, question:str, sequential_tasks: str, task_number: str) -> str:
    customer_profile=get_para("customerprofile")
    #return_str = ""
    task_json = dict()
    for key in node_json.keys():
        if not key.startswith("Metadata-"): 
            task_json[key] = node_json[key]
    task_str = json.dumps(task_json, ensure_ascii=False, indent=4)
    prompt_template_str = ''.join(get_para("sequential_taks_execution_prompt_template_first"))
    prompt_str = prompt_template_str.format(
        question=question, 
        customer_profile=customer_profile,
        task=task_str,
        task_number=task_number,
        sequential_tasks=sequential_tasks,
        language=get_para("language"),
        )
    return prompt_str

def generate_sequential_task_prompt_from_JSON_last(node_json: dict, node_type: str, question:str, sequential_tasks: str, task_number: str, input_from_previous_task) -> str:
    customer_profile=get_para("customerprofile")
    #return_str = ""
    task_json = dict()
    for key in node_json.keys():
        if not key.startswith("Metadata-"): 
            task_json[key] = node_json[key]
    task_str = json.dumps(task_json, ensure_ascii=False, indent=4)
    prompt_template_str = ''.join(get_para("sequential_taks_execution_prompt_template_last"))
    prompt_str = prompt_template_str.format(
        question=question, 
        customer_profile=customer_profile,
        task=task_str,
        task_number=task_number,
        sequential_tasks=sequential_tasks,
        input_from_previous_task=input_from_previous_task,
        language=get_para("language"),
        )
    return prompt_str