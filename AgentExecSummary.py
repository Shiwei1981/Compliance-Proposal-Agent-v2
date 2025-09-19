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
from AgentCommon import AgentState, generate_task_prompt_from_JSON, generate_summary_prompt_from_JSON, choose_mcp_tools



#做最后总结
def run_final_summary(state: AgentState):
    task_str = ""
    last_assistant_str = ""
    nodes_json = state["tasks_json"]["root"]
    for node in nodes_json:
        if node["Metadata-节点类型"] == "总述":
            try:
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
                node["输出"] = last_assistant_str
                node["Metadata-状态"] = "完成"  
                state["messages_history"].append(HumanMessage(task_str))
                state["messages_history"].append(AIMessage(last_assistant_str))
    return