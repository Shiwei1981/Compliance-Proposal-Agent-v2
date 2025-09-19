import json
from langgraph.graph import StateGraph, START, END
from langgraph.graph.message import add_messages
from AgentCommon import AgentState, logger
from AgentExecSerialArea import run_all_tasks, run_all_area_summaries
from AgentExecSummary import run_final_summary
from AgentExecAnalyze import analyze_one_time, analyze_area_to_area, analyze_area_to_serial_task, analyze_area_to_sequential_task



# 暂时不用了 langgraph 状态总是不对，怀疑是并发问题，加一个状态锁
state_json_task_status_lock = "release"

#一次性拆解节点，返回 JSON
def one_time_analyze_return_json(question: str, sessionid: str) -> dict:
    graph_builder = StateGraph(AgentState)

    graph_builder.add_node("analyze", analyze_one_time)
    graph_builder.add_edge(START, "analyze")
    graph_builder.add_edge("analyze", END)

    graph = graph_builder.compile()

    ##display(Image(graph.get_graph().draw_mermaid_png()))
    initial_state = {
        "messages": [], 
        "tasks_json": {}, 
        "question": question, 
        "messages_history": [],
        "direct_run": False,
        "sessionid": sessionid,
        }

    print(graph.get_graph().draw_mermaid())

    #trace
    logger.info(graph.get_graph().draw_mermaid())

    graph.invoke(initial_state)

    return initial_state["tasks_json"]

#以串行方式，一次性拆解节点，并直接执行
def one_time_analyze_run_graph_serial(question: str, sessionid: str) -> dict:
    graph_builder = StateGraph(AgentState)

    graph_builder.add_node("analyze", analyze_one_time)
    graph_builder.add_edge(START, "analyze")
    graph_builder.add_node("task", run_all_tasks)
    graph_builder.add_edge("analyze", "task")
    graph_builder.add_node("area", run_all_area_summaries)
    graph_builder.add_edge("task", "area")
    graph_builder.add_node("summary", run_final_summary)
    graph_builder.add_edge("area", "summary")
    graph_builder.add_edge("summary", END)

    graph = graph_builder.compile()

    ##display(Image(graph.get_graph().draw_mermaid_png()))
    initial_state = {
        "messages": [], 
        "tasks_json": {}, 
        "question": question, 
        "messages_history": [],
        "direct_run": False,
        "sessionid": sessionid
        }

    print(graph.get_graph().draw_mermaid())

    #trace
    logger.info(graph.get_graph().draw_mermaid())

    graph.invoke(initial_state)

    return initial_state["tasks_json"]

#直接接收 JSON，并执行 JSON
def direct_run_json(node_json: dict,question: str, sessionid: str) -> dict:
    # 直接运行一个任务
    graph_builder = StateGraph(AgentState)

    graph_builder.add_node("task", run_all_tasks)
    graph_builder.add_edge(START, "task")
    graph_builder.add_node("area", run_all_area_summaries)
    graph_builder.add_edge("task", "area")
    graph_builder.add_node("summary", run_final_summary)
    graph_builder.add_edge("area", "summary")
    graph_builder.add_edge("summary", END)

    graph = graph_builder.compile()

    initial_state = {
        "messages": [], 
        "tasks_json": node_json, 
        "question": question, 
        "messages_history": [],
        "direct_run": True,
        "sessionid":sessionid,
        }

    print(graph.get_graph().draw_mermaid())

    #trace
    logger.info(graph.get_graph().draw_mermaid())

    graph.invoke(initial_state)

    return initial_state["tasks_json"]

#将问题拆解为多个领域
def area_to_area(node_json: dict, area_message: str, node_number:str, question:str) -> dict:
    # 直接运行一个任务
    
    initial_state = {
        "messages": [], 
        "tasks_json": node_json, 
        "question": question, 
        "messages_history": [],
        "direct_run": False,
        "number_current_area": node_number,
        "message_area_to_area": area_message,
        }

    analyze_area_to_area(initial_state)

    return initial_state["tasks_json"]

#将领域拆解为串行任务
def area_to_serial_task(node_json: dict, area_message: str, node_number:str, question:str, sessionid:str) -> dict:
    # 直接运行一个任务
    graph_builder = StateGraph(AgentState)

    initial_state = {
        "messages": [], 
        "tasks_json": node_json, 
        "question": question, 
        "messages_history": [],
        "direct_run": False,
        "number_current_area": node_number,
        "message_area_to_area": area_message,
        "sessionid": sessionid,
        }

    analyze_area_to_serial_task(initial_state)

    return initial_state["tasks_json"]

#将领域拆解为顺序任务
def area_to_sequential_task(node_json: dict, area_message: str, node_number:str, question:str) -> dict:

    initial_state = {
        "messages": [], 
        "tasks_json": node_json, 
        "question": question, 
        "messages_history": [],
        "direct_run": False,
        "number_current_area": node_number,
        "message_area_to_area": area_message,
        }

    analyze_area_to_sequential_task(initial_state)

    return initial_state["tasks_json"]

#将领域拆解为并行任务


