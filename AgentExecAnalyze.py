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
from StaticVar import cal_toten, get_para, update_context, get_context_with_SessionID
from CommonFunc import LLM_Prompt_question_analyze
from mcp_csv_query.csv_query import get_csv_files_list, get_csv_schema
from AgentCommon import AgentState

#根据配置文件和问题，一次性拆解问题，并一次性形成json
def analyze_one_time(state: AgentState):
    csv_file_paths = [file['file_path'] for file in get_para("customer_CSV_files")]  
    csv_file_paths_str = ', '.join(f"'{file}'" for file in csv_file_paths)
    pdf_file_paths = [file['file_path'] for file in get_para("customer_PDF_files")]  
    pdf_file_paths_str = ', '.join(f"'{file}'" for file in pdf_file_paths)

    #字符串拼接两次
    question_analyze_prompt_message = " ".join(get_para("question_analyze_prompt_template")).format(
        customerprofile=get_para("customerprofile"),
        question=state["question"],
        methodologies=get_para("methodologies"),
        question_analyze_result_content=" ".join(get_para("question_analyze_result_content")),
        question_analyze_result_requirement=" ".join(get_para("question_analyze_result_requirement"))
    )

    question_analyze_prompt_message = question_analyze_prompt_message.format(
        area_number=get_para("area_number"),
        task_number=get_para("task_number"),
        customer_CSV_files=csv_file_paths_str,
        customer_PDF_files=pdf_file_paths_str,
        regulation_name=get_para("regulation_name"),
        language=get_para("language"),
        # o1 模型 每个任务 1W5 个 in_token, 2k5 个 out
    )

    #加入 csv file 和 schema
    file_names = get_csv_files_list()
    csv_schema_json = dict()
    for filename in file_names:
        result_file_schemas = get_csv_schema(filename)
        csv_schema_json[filename] = result_file_schemas
    csv_schema_str = json.dumps(csv_schema_json, ensure_ascii=False, indent=4)

    """
    # 临时代码 load prompt
    file_name = "example.txt"  
    # 读取 .txt 文件的内容  
    with open("example.txt", 'r', encoding='utf-8') as file:  
        question_analyze_prompt_message = file.read()  
    """
        
    question_analyze_prompt = [SystemMessage(get_para("question_analyze_system_prompt")), HumanMessage(question_analyze_prompt_message)]

    ##临时注释掉，为了测试 langgraph
    print("\n\n"+ datetime.now().strftime("%Y-%m-%d %H:%M:%S") + "\nPrompt: \n", question_analyze_prompt_message)
    response = LLM_Prompt_question_analyze(question_analyze_prompt)
    print("\n\n"+ datetime.now().strftime("%Y-%m-%d %H:%M:%S") + "\nResponse: \n", response)

    ## log
    msg_json = []
    for msg in question_analyze_prompt:  
        msg_json.append({  
            "role": msg.type,      # system／human  
            "content": msg.content # 消息文本  
        })  
    #question_analyze_prompt_json = [{"role": role, "message": message} for role, message in question_analyze_prompt]   
    with open('question_analyze_prompt.json', 'w', encoding='utf-8') as f:  
        json.dump(msg_json, f, ensure_ascii=False,indent=4)  
    question_analyze_reponse_json = json.loads(response)
    with open('question_analyze_response.json', 'w', encoding='utf-8') as f:  
        json.dump(question_analyze_reponse_json, f, ensure_ascii=False,indent=4)  
    
    ## 构造 测试数据
    with open('question_analyze_response.json', 'r', encoding='utf-8') as file: 
        question_analyze_response_json = json.load(file)  
    
    state["tasks_json"]['root'] = question_analyze_response_json['root']
    context = get_context_with_SessionID(state["sessionid"])
    context.task_json = question_analyze_response_json
    update_context(context)
    return

#客户问题分解为多个领域
def analyze_area_to_area(state: AgentState) -> dict:
    csv_file_paths = [file['file_path'] for file in get_para("customer_CSV_files")]  
    csv_file_paths_str = ', '.join(f"'{file}'" for file in csv_file_paths)
    pdf_file_paths = [file['file_path'] for file in get_para("customer_PDF_files")]  
    pdf_file_paths_str = ', '.join(f"'{file}'" for file in pdf_file_paths)

    area_to_area_prompt_str = " ".join(get_para("area_to_area_prompt_template")).format(
        customerprofile=get_para("customerprofile"),
        question=state["question"],
        methodologies=get_para("methodologies"),
        message_area=state["message_area_to_area"],
        node_number=state["number_current_area"],
        area_to_area_requirement=" ".join(get_para("area_to_area_requirement")),
        area_to_area_content=" ".join(get_para("area_to_area_content"))
    )

    area_to_area_prompt_str = area_to_area_prompt_str.format(
        area_number=get_para("area_number"),
        customer_CSV_files=csv_file_paths_str,
        customer_PDF_files=pdf_file_paths_str
        # o1 模型 每个任务 1W5 个 in_token, 2k5 个 out
    )

    area_to_area_prompt = [HumanMessage(area_to_area_prompt_str)]
    response = LLM_Prompt_question_analyze(area_to_area_prompt)
    area_json = json.loads(response)

    return_json = dict()
    return_json['root'] = []

    for item in area_json['root']:
        #如果是该节点，或子节点
        if item["Metadata-节点编号"] == state["number_current_area"] or item["Metadata-节点编号"].startswith(state["number_current_area"]):
            return_json['root'].append(item)

    for item in state["tasks_json"]['root']:
        #如果是该节点，或子节点，则跳过
        if item["Metadata-节点编号"] == state["number_current_area"] or item["Metadata-节点编号"].startswith(state["number_current_area"]):
            continue
        #如果不是该节点 或 子节点，则添加
        else:
            return_json['root'].append(item)

    state["tasks_json"] = return_json
    return return_json

#将领域拆解为串行任务
def analyze_area_to_serial_task(state: AgentState) -> dict:
    csv_file_paths = [file['file_path'] for file in get_para("customer_CSV_files")]  
    csv_file_paths_str = ', '.join(f"'{file}'" for file in csv_file_paths)
    pdf_file_paths = [file['file_path'] for file in get_para("customer_PDF_files")]  
    pdf_file_paths_str = ', '.join(f"'{file}'" for file in pdf_file_paths)

    area_to_serial_task_prompt_str = " ".join(get_para("area_to_serial_task_prompt_template")).format(
        customerprofile=get_para("customerprofile"),
        question=state["question"],
        methodologies=get_para("methodologies"),
        message_area=state["message_area_to_serial_task"],
        node_number=state["number_current_area"],
        area_to_serial_task_requirement=" ".join(get_para("area_to_serial_task_requirement")),
        area_to_serial_task_content=" ".join(get_para("area_to_serial_task_content"))
    )

    area_to_serial_task_prompt_str = area_to_serial_task_prompt_str.format(
        area_number=get_para("area_number"),
        customer_CSV_files=csv_file_paths_str,
        customer_PDF_files=pdf_file_paths_str
        # o1 模型 每个任务 1W5 个 in_token, 2k5 个 out
    )

    area_to_serial_task_prompt = [HumanMessage(area_to_serial_task_prompt_str)]
    response = LLM_Prompt_question_analyze(area_to_serial_task_prompt)
    area_json = json.loads(response)

    return_json = dict()
    return_json['root'] = []

    for item in area_json['root']:
        #如果是该节点，或子节点
        if item["Metadata-节点编号"] == state["number_current_area"] or item["Metadata-节点编号"].startswith(state["number_current_area"]):
            return_json['root'].append(item)

    for item in state["tasks_json"]['root']:
        #如果是该节点，或子节点，则跳过
        if item["Metadata-节点编号"] == state["number_current_area"] or item["Metadata-节点编号"].startswith(state["number_current_area"]):
            continue
        #如果不是该节点 或 子节点，则添加
        else:
            return_json['root'].append(item)

    state["tasks_json"] = return_json
    return  return_json

#将领域拆解为顺序任务
def analyze_area_to_sequential_task(state: AgentState) -> dict:
    csv_file_paths = [file['file_path'] for file in get_para("customer_CSV_files")]  
    csv_file_paths_str = ', '.join(f"'{file}'" for file in csv_file_paths)
    pdf_file_paths = [file['file_path'] for file in get_para("customer_PDF_files")]  
    pdf_file_paths_str = ', '.join(f"'{file}'" for file in pdf_file_paths)

    area_to_sequential_task_prompt_str = " ".join(get_para("area_to_sequential_task_prompt_template")).format(
        customerprofile=get_para("customerprofile"),
        question=state["question"],
        methodologies=get_para("methodologies"),
        message_area=state["message_area_to_sequential_task"],
        node_number=state["number_current_area"],
        area_to_sequential_task_requirement=" ".join(get_para("area_to_sequential_task_requirement")),
        area_to_sequential_task_content=" ".join(get_para("area_to_sequential_task_content"))
    )

    area_to_sequential_task_prompt_str = area_to_sequential_task_prompt_str.format(
        area_number=get_para("area_number"),
        customer_CSV_files=csv_file_paths_str,
        customer_PDF_files=pdf_file_paths_str
        # o1 模型 每个任务 1W5 个 in_token, 2k5 个 out
    )

    area_to_sequential_task_prompt = [HumanMessage(area_to_sequential_task_prompt_str)]
    response = LLM_Prompt_question_analyze(area_to_sequential_task_prompt)
    area_json = json.loads(response)

    return_json = dict()
    return_json['root'] = []

    for item in area_json['root']:
        #如果是该节点，或子节点
        if item["Metadata-节点编号"] == state["number_current_area"] or item["Metadata-节点编号"].startswith(state["number_current_area"]):
            return_json['root'].append(item)

    for item in state["tasks_json"]['root']:
        #如果是该节点，或子节点，则跳过
        if item["Metadata-节点编号"] == state["number_current_area"] or item["Metadata-节点编号"].startswith(state["number_current_area"]):
            continue
        #如果不是该节点 或 子节点，则添加
        else:
            return_json['root'].append(item)

    state["tasks_json"] = return_json
    return  return_json
