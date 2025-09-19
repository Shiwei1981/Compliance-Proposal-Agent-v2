import re 
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
from AgentCommon import AgentState, generate_task_prompt_from_JSON, generate_summary_prompt_from_JSON, choose_mcp_tools, generate_sequential_task_prompt_from_JSON, generate_sequential_task_prompt_from_JSON_first, generate_sequential_task_prompt_from_JSON_last

#执行所有可执行的 顺序任务 Task
def run_all_sequential_tasks(state: AgentState):
    task_str = ""
    last_assistant_str = ""
    nodes_json = state["tasks_json"]["root"]
    for node in nodes_json:
        #首先找到顺序领域，
        if node["Metadata-节点类型"] == "顺序领域":
            #制作顺序任务编号数组，这里选择使用循环而不直接分解 子节点 字段。主要是怕他错。
            area_number = node["Metadata-节点编号"]
            task_totalnumber = 0
            for node_sequential_task in nodes_json:
                if node_sequential_task["Metadata-节点编号"].startswith(area_number) and node_sequential_task["Metadata-节点编号"] != area_number:
                    task_totalnumber = task_totalnumber+1
            sequential_tasks_json = [dict()]
            for i in range(1, task_totalnumber):
                for sequential_task in nodes_json:
                    if ["Metadata-节点编号"] == area_number + "." + str(i):          
                        sequential_tasks_json.append(sequential_task)
            #按顺序执行 顺序任务    
            for i in range(1, task_totalnumber):
                for sequential_task in nodes_json:
                    if sequential_task["Metadata-节点编号"] == area_number + "." + str(i):                        
                        try:
                            sequential_task["Metadata-状态"] = "开始执行" 
                            state["current_task"] = sequential_task["Metadata-节点编号"] 
                            if i == 1:
                                task_str = generate_sequential_task_prompt_from_JSON_first(
                                    node_json=sequential_task, 
                                    node_type=sequential_task["Metadata-节点类型"], 
                                    question=state["question"],
                                    sequential_tasks=str(sequential_tasks_json),
                                    task_number=sequential_task["Metadata-节点编号"])
                            elif i == task_totalnumber:
                                task_str = generate_sequential_task_prompt_from_JSON_last(
                                    node_json=sequential_task, 
                                    node_type=sequential_task["Metadata-节点类型"], 
                                    question=state["question"],
                                    sequential_tasks=str(sequential_tasks_json),
                                    task_number=sequential_task["Metadata-节点编号"],
                                    input_from_previous_task=state["message_sequential_task_to_sequential_task"])
                            else:
                                task_str = generate_sequential_task_prompt_from_JSON(
                                    node_json=sequential_task, 
                                    node_type=sequential_task["Metadata-节点类型"], 
                                    question=state["question"],
                                    sequential_tasks=str(sequential_tasks_json),
                                    task_number=sequential_task["Metadata-节点编号"],
                                    input_from_previous_task=state["message_sequential_task_to_sequential_task"])

                            tool_list = choose_mcp_tools(sequential_task)
                            messages =  asyncio.run(mcp_init_and_process_query(task_str, tool_list))
                            for message in messages:  
                                if message["role"] == "assistant":  
                                    last_assistant_str = last_assistant_str + "\n---\n" + message["content"]
                                else:
                                    last_assistant_str = "" 
                            pattern = r'<output_to_next_task>(.*?)</output_to_next_task>'  
                            matches = re.findall(pattern, last_assistant_str, re.DOTALL)               
                        finally:
                            update_context_output(state['sessionid'], last_assistant_str, sequential_task["Metadata-节点编号"])
                            sequential_task["输出至下一个任务"] = matches
                            state["message_sequential_task_to_sequential_task"] = matches
                            sequential_task["输出"] = last_assistant_str
                            sequential_task["Metadata-状态"] = "完成"  
                            state["messages_history"].append(HumanMessage(task_str))
                            state["messages_history"].append(AIMessage(last_assistant_str))
    return

#总结所有可以总结的 Area - 暂时不使用， 使用 Serial Task Summary 应该也可以做到相同的结果。
def run_all_sequential_area_summaries(state: AgentState):
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

