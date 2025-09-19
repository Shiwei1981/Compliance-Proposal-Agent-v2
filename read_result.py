import json
from fpdf import FPDF
import os

class PDF(FPDF):  
    def header(self):  
        self.set_font("Arial", "B", 12)  
        self.cell(0, 10, "PDF Header", 0, 1, "C")  
  
    def footer(self):  
        self.set_y(-15)  
        self.set_font("Arial", "I", 8)  
        self.cell(0, 10, f"Page {self.page_no()}", 0, 0, "C")  

question_analyze_result_json = dict()
with open('question_analyze_result.json', 'r', encoding='utf-8') as file: 
    question_analyze_result_json = json.load(file)

for item in question_analyze_result_json:

    print(item['分析任务名称'])
    print('\n')
    print(item['输出'])
    print('\n')
    #input('回车输出PDF,并展示下一个结果')
    pdf = PDF()  
    pdf.add_page()  

    filename = 'output_pdf\\【' + item['Metadata-节点编号'] + '】' + item['分析任务名称'] + '.md'
    # 将字符串写入 .md 文件  
    if os.path.exists(filename):  
        os.remove(filename) 
    with open(filename, 'w', encoding='utf-8') as file:  
        file.write(item['输出'])  

    """
    filename = 'output_pdf\\【' + item['Metadata-节点类型'] + '】'+ item['分析任务名称'] + '.pdf'
    if os.path.exists(item['输出']):  
        os.remove(item['输出'])  
    print(item['分析任务名称'])
    print('\n')
    print(item['输出'])
    print('\n')
    input('回车输出PDF,并展示下一个结果')
    pdf = PDF()  
    pdf.add_page()  
    
    # 设置字体  
    pdf.add_font("MicrosoftYaHei", "", "msyh.ttc", uni=True)  # 使用 Arial Unicode 字体  
    pdf.set_font("MicrosoftYaHei", size=10) 
    
    # 使用 multi_cell() 方法添加长文本  
    pdf.multi_cell(0, 6, item['输出'])  
    #pdf.multi_cell(0, 10, '测试文本')  

    # 输出 PDF 文件  
    pdf.output(filename)
    """
