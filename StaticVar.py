import tiktoken
import os
import json

api_key = os.getenv("AZURE_OPENAI_API_KEY")  
endpoint = os.getenv("AZURE_OPENAI_ENDPOINT")  
api_version = os.getenv("AZURE_OPENAI_API_VERSION")
model_name = os.getenv("AZURE_OPENAI_MODEL_NAME") 
model_name_emb = os.getenv("AZURE_OPENAI_MODEL_NAME_EMB") 
model_name_reasoning = os.getenv("AZURE_OPENAI_MODEL_NAME_REASONING") 
model_name_reasoning_mini = os.getenv("AZURE_OPENAI_MODEL_NAME_REASONING_MINI") 

total_token = dict()

def cal_toten(model_name:str, prompt_str:str, output:str):
    global total_token
    total_in = 0
    total_out = 0
    for entry in total_token:  
        if entry == model_name:  
            total_in = total_token[entry]["total_token_in"]  
            total_out = total_token[entry]["total_token_out"]  
            break  
    encoding = tiktoken.get_encoding("cl100k_base")  
    total_in = total_in + len(encoding.encode(prompt_str))
    if output is not None:
        total_out = total_out + len(encoding.encode(output))
    total_token[model_name] = {"total_token_in": total_in, "total_token_out": total_out}

def print_toten()->str:
    global total_token
    return_str = json.dumps(total_token, indent=4, ensure_ascii=False)
    print(return_str)
    return return_str


def get_para(paraname: str) -> str:  
    try:  
        # 尝试打开 config.json 文件  
        with open('config.json', encoding='utf-8') as config_file:  
            config_data = json.load(config_file)  
    except FileNotFoundError:  
        raise Exception("Config file 'config.json' not found.")  
    except json.JSONDecodeError:  
        raise Exception("Error decoding JSON from 'config.json'.")  
    except Exception as e:  
        raise Exception(f"An unexpected error occurred: {e}")  
    # 检查参数是否存在于配置数据中  
    if paraname not in config_data:  
        raise Exception("Can't find value in config.json")  
    result = config_data[paraname]  
    # 如果值为 None 或者空字符串，也抛出异常  
    if result is None or result == "":  
        raise Exception("Value in config.json is empty or None")  
    
    return result  



# 定义CommonAgentContext类  
class CommonAgentContext:
    def __init__(self, sessionID):  
        self.sessionID = sessionID  # 定义属性 name  
        self.messages_history = [] # 消息历史记录
        self.customerprofile = get_para("customerprofile")
        self.activity_content = {} # JSON 对象 包含每一个 activity 的输出结果
        self.customer_CSV_files = get_para("customer_CSV_files")
        self.customer_PDF_files = get_para("customer_PDF_files")
        self.question_analyze_prompt_template = " ".join(get_para("question_analyze_prompt_template"))
        self.question_analyze_result_content = " ".join(get_para("question_analyze_result_content"))
        self.question_analyze_result_requirement = " ".join(get_para("question_analyze_result_requirement"))
        self.question_analyze_system_prompt = get_para("question_analyze_system_prompt")
        self.question = ""
        self.task_json = dict()


contexts = []

def remove_context(sessionID:str):
    contexts.remove(get_context_with_SessionID(sessionID))

def update_context(context:CommonAgentContext):
    for obj in contexts:  
        if (obj.sessionID == context.sessionID):
            obj = context

def get_context_with_SessionID(sessionID:str) -> CommonAgentContext:
    bexist = False
    for obj in contexts:  
        if (obj.sessionID == sessionID):
            bexist = True
            return obj
    if not bexist:
        context = CommonAgentContext(sessionID)
        contexts.append(context)
    return context

def save_context_activity_content(sessionID:str):
    context = get_context_with_SessionID(sessionID)
    json_file_path = 'save_context_activity_content.json'  
    with open(json_file_path, 'w', encoding='utf-8') as file:  
        json.dump(context.activity_content, file, ensure_ascii=False, indent=4)  

def update_context_output(sessionID:str, output_str:str, node_number_str: str):
    context = get_context_with_SessionID(sessionID=sessionID)
    for item in context.task_json['root']:
        if item['Metadata-节点编号'] == node_number_str:
            item['Metadata-状态'] = "完成"
            item['输出'] = output_str
            return


