from typing import List
from langchain_openai import AzureChatOpenAI
from typing import TypedDict, Annotated,List
from StaticVar import api_key, endpoint, api_version, model_name, model_name_emb, model_name_reasoning, model_name_reasoning_mini
from StaticVar import cal_toten
from StaticVar import get_para


env={
        "AZURE_OPENAI_API_KEY":api_key,
        "AZURE_OPENAI_ENDPOINT":endpoint,
        "AZURE_OPENAI_API_VERSION":api_version,
        "AZURE_OPENAI_MODEL_NAME":model_name,
        "AZURE_OPENAI_MODEL_NAME_EMB":model_name_emb        
    } 

def LLM_Prompt_question_analyze(messages: List[str]) -> str:
    model = AzureChatOpenAI(
        api_key=api_key,
        azure_endpoint=endpoint,
        api_version=api_version,
        model=model_name_reasoning
    )
    response = model.invoke(messages)
    contents = [message.content for message in messages]  
    prompt_str = "".join(contents)  
    cal_toten(model_name = model_name_reasoning, prompt_str=prompt_str, output = response.content)
    return response.content

def LLM_Prompt_task_execute(messages: List[str]) -> str:
    model = AzureChatOpenAI(
        api_key=api_key,
        azure_endpoint=endpoint,
        api_version=api_version,
        model=model_name,
        temperature=0
    )    
    response = model.invoke(messages)
    contents = [message.content for message in messages]  
    prompt_str = "".join(contents)  
    cal_toten(model_name = model_name_reasoning, prompt_str=prompt_str, output = response.content)
    return response.content

def LLM_Prompt_outcome_summarize(messages: List[str]) -> str:
    model = AzureChatOpenAI(
        api_key=api_key,
        azure_endpoint=endpoint,
        api_version=api_version,
        model=model_name,
        temperature=0
    )    
    response = model.invoke(messages)
    contents = [message.content for message in messages]  
    prompt_str = "".join(contents)  
    cal_toten(model_name = model_name_reasoning, prompt_str=prompt_str, output = response.content)
    return response.content

