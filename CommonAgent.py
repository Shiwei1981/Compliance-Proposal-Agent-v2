import json
from typing import List 
from CommonFunc import get_para, LLM_Prompt_question_analyze
from AgentOrchestrator import one_time_analyze_run_graph_serial, one_time_analyze_return_json, direct_run_json, area_to_area, area_to_serial_task, area_to_sequential_task
from langgraph.graph import START, END
from langchain_core.messages import SystemMessage, HumanMessage, AIMessage
import asyncio
from MCPClientManager import mcp_init_and_process_query, mcp_tools_class
from StaticVar import print_toten, CommonAgentContext, get_para, get_context_with_SessionID, update_context, remove_context

# 定义CommonAgent类  
class CommonAgent:  
    # 初始化方法，__init__ 是一个特殊方法，用于初始化对象  
    def __init__(self, context:CommonAgentContext):  
        self.context = context

    # 定义 answerquestion 方法  
    def answerquestion(self, question: str, sessionID:str):          
        self.context = get_context_with_SessionID(sessionID)  
        self.context.question = question
        question_analyze_result = one_time_analyze_run_graph_serial(self.context.question, sessionid=sessionID)
        with open('question_analyze_result.json', 'w', encoding='utf-8') as f:  
            json.dump(question_analyze_result['root'], f, ensure_ascii=False,indent=4) 
        self.context.task_json = question_analyze_result  
        print('\n\nquestion answered!')  
        json_str = json.dumps(question_analyze_result, ensure_ascii=False, indent=4)  
        return json_str  
    
     # 定义 answerquestion 方法  
    def analyzequestion(self, question: str, sessionID:str):          
        self.context = get_context_with_SessionID(sessionID)  
        self.context.question = question
        question_analyze_result = one_time_analyze_return_json(self.context.question, sessionid=sessionID)
        with open('question_analyze_response.json', 'w', encoding='utf-8') as f:  
            json.dump(question_analyze_result['root'], f, ensure_ascii=False,indent=4) 
        self.context.task_json = question_analyze_result  
        json_str = json.dumps(question_analyze_result, ensure_ascii=False, indent=4)  
        return json_str  

    # 定义 quickquery 方法  
    def quickquery(self, question: str):  
        prompt_template_str = get_para("quick_query_prompt_template")
        tool_list = mcp_tools_class()
        tool_list.MCP_PDF = "enable"
        tool_list.MCP_CSV = "enable"
        tool_list.MCP_DDGWEBSEARCH = "enable"
        messages =  asyncio.run(mcp_init_and_process_query(prompt_template_str.format(question=question), tool_list))
        last_assistant_str = ""
        for message in messages:  
            if message["role"] == "assistant":  
                last_assistant_str = message["content"]   
        return last_assistant_str

    def run_json(self, json_str: str, question: str, sessionID:str):  
        self.context = get_context_with_SessionID(sessionID)  
        self.context.question = question
        node_json = json.loads(json_str)
        question_analyze_result = direct_run_json(question=question, node_json=node_json, sessionid=sessionID)
        with open('question_analyze_result.json', 'w', encoding='utf-8') as f:  
            json.dump(question_analyze_result['root'], f, ensure_ascii=False,indent=4) 
        self.context.task_json = question_analyze_result  
        json_str = json.dumps(question_analyze_result, ensure_ascii=False, indent=4)  
        return json_str  

    # 领域拆解领域    
    def analyze_area_to_area(self, question: str, sessionID:str, node_number:str):  
        self.context.question = question
        area_message = ""
        for area in self.context.task_json['root']:
            if area['Metadata-节点编号'] == node_number:
                area_message = area['分析领域']
                break
        if node_number == "1":
            area_message = question
        analyze_area_to_area_result = area_to_area(
            node_json=self.context.task_json,
            node_number=node_number,
            question=question,
            area_message=area_message,
            )
 
        json_str = json.dumps(analyze_area_to_area_result, ensure_ascii=False, indent=4)  
        return json_str

    # 领域拆解为串行任务
    def analyze_area_to_serial_task(self, question: str, sessionID:str, node_number:str):  
        self.context.question = question
        area_message = ""
        for area in self.context.task_json['root']:
            if area['Metadata-节点编号'] == node_number:
                area_message = area['分析领域']
                break
        if node_number == "1":
            area_message = question
        analyze_area_to_area_result = area_to_serial_task(
            node_json=self.context.task_json,
            node_number=node_number,
            question=question,
            area_message=area_message,
            sessionid=sessionID,
            )
 
        json_str = json.dumps(analyze_area_to_area_result, ensure_ascii=False, indent=4)  
        return json_str

    #领域拆解为顺序任务
    def analyze_area_to_sequential_task(self, question: str, sessionID:str, node_number:str):  
        self.context.question = question
        area_message = ""
        for area in self.context.task_json['root']:
            if area['Metadata-节点编号'] == node_number:
                area_message = area['分析领域']
                break
        if node_number == "1":
            area_message = question
        analyze_area_to_area_result = area_to_sequential_task(
            node_json=self.context.task_json,
            node_number=node_number,
            question=question,
            area_message=area_message,
            )
 
        json_str = json.dumps(analyze_area_to_area_result, ensure_ascii=False, indent=4)  
        return json_str


