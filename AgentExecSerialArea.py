
import json
from langchain_openai import AzureChatOpenAI
from typing_extensions import TypedDict
from langgraph.graph.message import AnyMessage
from langchain_core.messages import AIMessage, HumanMessage, SystemMessage
from langgraph.graph import StateGraph, START, END
from typing import TypedDict, Annotated,List
from IPython.display import Image, display
from datetime import datetime
from MCPClientManager import mcp_init_and_process_query, mcp_tools_class
import asyncio
from StaticVar import api_key, endpoint, api_version, model_name, model_name_emb, model_name_reasoning, model_name_reasoning_mini
from StaticVar import cal_toten, get_para, update_context_output
from CommonFunc import LLM_Prompt_question_analyze
from mcp_csv_query.csv_query import get_csv_files_list, get_csv_schema
from AgentCommon import AgentState, generate_task_prompt_from_JSON, generate_summary_prompt_from_JSON, choose_mcp_tools

#执行所有可执行的 Task
def run_all_tasks(state: AgentState):
    task_str = ""
    last_assistant_str = ""
    nodes_json = state["tasks_json"]["root"]
    for node in nodes_json:
        if node["Metadata-节点类型"] == "分析任务":
            try:
                node["Metadata-状态"] = "开始执行" 
                state["current_task"] = node["Metadata-节点编号"] 
                task_str = generate_task_prompt_from_JSON(node, node["Metadata-节点类型"], question=state["question"])
                tool_list = choose_mcp_tools(node)
                messages =  asyncio.run(mcp_init_and_process_query(task_str, tool_list))
                for message in messages:  
                    if message["role"] == "assistant":  
                        last_assistant_str = last_assistant_str + "\n---\n" + message["content"]
                    else:
                        last_assistant_str = ""                
            finally:
                update_context_output(state['sessionid'], last_assistant_str, node["Metadata-节点编号"])
                node["输出"] = last_assistant_str
                node["Metadata-状态"] = "完成"  
                state["messages_history"].append(HumanMessage(task_str))
                state["messages_history"].append(AIMessage(last_assistant_str))
    return

#总结所有可以总结的 Area
def run_all_area_summaries(state: AgentState):
    task_str = ""
    last_assistant_str = ""
    nodes_json = state["tasks_json"]["root"]
    for node in nodes_json:
        if node["Metadata-节点类型"] == "分析领域":
            try:
            ##首先决定做哪一个task，寻找第一个状态是 "待分析" 的 task
                node["Metadata-状态"] = "开始总结"  
                state["current_task"] = node["Metadata-节点编号"] 
                previouse_outputs = ""
                for node_child in state["tasks_json"]["root"]:
                    if node_child['Metadata-父节点编号'] == node["Metadata-节点编号"]:  
                        previouse_outputs = previouse_outputs + "\n\n --- \n" + node_child['输出']
                summary_prompt_str = generate_summary_prompt_from_JSON(
                    question=state["question"],
                    previouse_messages_str=previouse_outputs
                )
                messages = [HumanMessage(summary_prompt_str)]
                LLM = AzureChatOpenAI(
                    api_key=api_key,
                    api_version=api_version,
                    azure_endpoint=endpoint,
                    azure_deployment=model_name
                )
                response = LLM.invoke(messages)
                last_assistant_str = response.content
            finally:
                update_context_output(state['sessionid'], last_assistant_str, node["Metadata-节点编号"])
                node["输出"] = last_assistant_str
                node["Metadata-状态"] = "完成"  
                state["messages_history"].append(HumanMessage(task_str))
                state["messages_history"].append(AIMessage(last_assistant_str))
    return


def conditional_edge_area_next(state: AgentState) -> str:
    # 这里可以根据状态的值来决定是否添加边
    if state["current_task"] == "task_1":
        return "area"
    else:
        return "summary"
