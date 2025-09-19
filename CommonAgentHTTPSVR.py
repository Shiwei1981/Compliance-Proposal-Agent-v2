from http.server import SimpleHTTPRequestHandler, HTTPServer  
import urllib.parse  
import json  
from CommonAgent import CommonAgent
from StaticVar import print_toten, CommonAgentContext, get_para, get_context_with_SessionID, update_context, remove_context

# 定义请求处理类，继承自 SimpleHTTPRequestHandler  
class MyHandler(SimpleHTTPRequestHandler):  
    global contexts
    # 新增：处理 OPTIONS 预检请求  
    def do_OPTIONS(self):  
        self.send_response(200, "ok")  
        self.send_header("Access-Control-Allow-Origin", "*")  
        self.send_header("Access-Control-Allow-Methods", "POST, GET, OPTIONS")  
        self.send_header("Access-Control-Allow-Headers", "Content-Type, Accept")  
        self.end_headers()  

    # 处理 POST 请求  
    def do_POST(self):  
        content_length = int(self.headers['Content-Length'])  
        post_data = self.rfile.read(content_length).decode('utf-8')  

        # 尝试解析 JSON，解析失败则返回 400  
        try:  
            data = json.loads(post_data)  
        except json.JSONDecodeError:  
            self.send_error(400, "Bad Request: Invalid JSON")  
            return  

        if self.path == "/answerquestion":  
            # 检查必需字段  
            if "question" in data and "sessionid" in data:  
                question = data["question"]  
                sessionid = data["sessionid"]  

                agent = CommonAgent(get_context_with_SessionID(sessionid))  
                result = agent.answerquestion(question, sessionID=sessionid)  
                update_context(agent.context)  

                json_str = json.dumps(agent.context.task_json, ensure_ascii=False, indent=4)  
                self.respond(json_str)  
            else:  
                self.send_error(400, "Bad Request: missing parameter")  

        elif self.path == "/analyzequestion":  
            if "question" in data and "sessionid" in data:  
                question = data["question"]  
                sessionid = data["sessionid"]  

                agent = CommonAgent(get_context_with_SessionID(sessionid))  
                result = agent.analyzequestion(question, sessionID=sessionid)  
                update_context(agent.context)  

                json_str = json.dumps(agent.context.task_json, ensure_ascii=False, indent=4)  
                self.respond(json_str)  
            else:  
                self.send_error(400, "Bad Request: missing parameter")  

        elif self.path == "/quickquery":  
            if "question" in data and "sessionid" in data:  
                question = data["question"]  
                sessionid = data["sessionid"]  

                agent = CommonAgent(get_context_with_SessionID(sessionid))  
                result = agent.quickquery(question)  
                update_context(agent.context)  
 
                self.respond(result)  
            else:  
                self.send_error(400, "Bad Request: missing parameter")  

        elif self.path == "/gettoken":  
            # 无需参数，直接调用  
            result = print_toten()  
            self.respond(result)  

        elif self.path == "/syncjson":  
            if "sessionid" in data:  
                sessionid = data["sessionid"]  
                context = get_context_with_SessionID(sessionid)  

                json_str = json.dumps(context.task_json, ensure_ascii=False, indent=4)  
                self.respond(json_str)  
            else:  
                self.send_error(400, "Bad Request: missing 'sessionid' parameter")  

        elif self.path == "/runjson":  
            if "taskjson" in data and "sessionid" in data and "question" in data:  
                taskjson_str = data["taskjson"]  
                sessionid = data["sessionid"]  
                question = data["question"]  

                agent = CommonAgent(get_context_with_SessionID(sessionid))  
                agent.context.task_json = json.loads(taskjson_str)
                agent.context.question = question
                agent.run_json(json_str=taskjson_str, question=question, sessionID=sessionid)

                update_context(agent.context)

                json_str = json.dumps(agent.context.task_json, ensure_ascii=False, indent=4)  
                self.respond(json_str)  
            else:  
                self.send_error(400, "Bad Request: missing parameter")  

        elif self.path == "/submitjson":  
            if "taskjson" in data and "sessionid" in data:  
                taskjson = data["taskjson"]  
                sessionid = data["sessionid"]  

                agent = CommonAgent(get_context_with_SessionID(sessionid))  
                agent.context.task_json = json.loads(taskjson) 
                update_context(agent.context)  

                self.respond(taskjson)  
            else:  
                self.send_error(400, "Bad Request: missing parameter")  

        elif self.path == "/areatoarea":  
            if "taskjson" in data and "sessionid" in data and "question" in data and "nodenumber" in data:  
                taskjson = data["taskjson"]  
                sessionid = data["sessionid"] 
                question = data["question"] 
                nodenumber = data["nodenumber"] 

                agent = CommonAgent(get_context_with_SessionID(sessionid))  
                agent.context.task_json = json.loads(taskjson) 
                return_str = agent.analyze_area_to_area(
                    question=question, sessionID=sessionid, node_number=nodenumber
                )
                self.respond(return_str)  
            else:  
                self.send_error(400, "Bad Request: missing parameter")  

        elif self.path == "/areatoserialtask":  
            if "taskjson" in data and "sessionid" in data and "question" in data and "nodenumber" in data:  
                taskjson = data["taskjson"]  
                sessionid = data["sessionid"] 
                question = data["question"] 
                nodenumber = data["nodenumber"] 

                agent = CommonAgent(get_context_with_SessionID(sessionid))  
                agent.context.task_json = json.loads(taskjson) 
                return_str = agent.analyze_area_to_serial_task(
                    question=question, sessionID=sessionid, node_number=nodenumber
                )
                self.respond(return_str)  
            else:  
                self.send_error(400, "Bad Request: missing parameter")  

        elif self.path == "/areatosequentialtask":  
            if "taskjson" in data and "sessionid" in data and "question" in data and "nodenumber" in data:  
                taskjson = data["taskjson"]  
                sessionid = data["sessionid"] 
                question = data["question"] 
                nodenumber = data["nodenumber"] 

                agent = CommonAgent(get_context_with_SessionID(sessionid))  
                agent.context.task_json = json.loads(taskjson) 
                return_str = agent.analyze_area_to_sequential_task(
                    question=question, sessionID=sessionid, node_number=nodenumber
                )
                self.respond(return_str)  
            else:  
                self.send_error(400, "Bad Request: missing parameter")  

        else:  
            self.send_error(404, "Not Found")  

    # 返回 HTTP 响应（添加跨域头）  
    def respond(self, message):  
        self.send_response(200)  
        self.send_header("Content-type", "application/json; charset=utf-8")  
        # 必需的跨域头，允许浏览器访问  
        self.send_header("Access-Control-Allow-Origin", "*")  
        self.send_header("Access-Control-Allow-Methods", "POST, GET, OPTIONS")  
        self.send_header("Access-Control-Allow-Headers", "Content-Type, Accept")  
        self.end_headers()  
        self.wfile.write(message.encode())  
  
# 启动 HTTP 服务器  
def run(server_class=HTTPServer, handler_class=MyHandler, port=8000):  
    server_address = ('', port)  
    httpd = server_class(server_address, handler_class)  
    print(f"Serving on port {port}...")  
    httpd.serve_forever()  
  
# 主函数  
def main():  
    run() 

if __name__ == "__main__":  
    main()  