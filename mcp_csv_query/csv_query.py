import argparse
from typing import List, Dict, Any, Optional
from pydantic import Field
from mcp.server.fastmcp import FastMCP
from glob import glob
import pandas as pd  
import sqlite3  


parser = argparse.ArgumentParser()
#发现 function call 的时候，路径有时候会丢失，索性就放在程序根目录吧
parser.add_argument("--file_location", type=str, default="./*.csv")
args = parser.parse_args()


mcp = FastMCP("mcp_csv_query", dependencies=["polars"])


@mcp.tool()
def get_csv_files_list() -> str:
    """
    This tool can returns the list of CSV file names that are source of data.
    Cannot read PDF files.
    """
    files_list = glob(args.file_location)
    return files_list


def read_file(
    file_location: str,
) -> pd.DataFrame:
    """
    Read the data from the given file location.
    """
    file_location = file_location.lower()
    if not file_location.endswith('.csv'):  
    # 如果不是，则添加 .csv 扩展名  
        file_location += '.csv'  
    return pd.read_csv(file_location)

@mcp.tool()
def get_csv_schema(
    file_location: str) -> List[Dict[str, Any]]:
    """
    This tool can obtain the schema information of the corporate data file in CSV format provided by the customer.
    Get the schema of a single data file from the given file location.    
    Cannot read PDF files.
    """
    df = read_file(file_location)

    schema = {col: str(df[col].dtype) for col in df.columns}
    #schema = df.schema
    #schema_dict = {}
    #for key, value in schema.items():
        #schema_dict[key] = value
    return schema


query_description = f"""
Supports the use of standard SQL syntax run in SQLite. 
"""

@mcp.tool()
def execute_sql_query_csv(
    file_locations: List[str],
    query: str = Field(
        description=query_description,
    )
) -> List[Dict[str, Any]]:
    """
    This tool can explore the data of corporate data files in CSV format provided by the client and supports joint queries across multiple CSV file_locations.
    In the query, use the filename of the CSV as the table name replace "self" in query script, and making sure to exclude the file extension for clarity.
    Cannot read PDF files.
    """ 

    # 创建一个 SQLite 数据库 in-memory  
    conn = sqlite3.connect(':memory:')  
    
    # 遍历每个 CSV 文件并加载到 SQLite 数据库中  
    for filename in file_locations:  
        filename = filename.lower()
        if not filename.endswith('.csv'):  
            filename = filename + '.csv'  
        df = pd.read_csv(filename)  
        
        # 去掉 '\' 及之前的内容  
        table_name = filename.split('\\')[-1]  
        
        # 去掉 '/' 及之前的内容  
        table_name = table_name.split('/')[-1]  
        
        # 去掉 '.csv' 及以后的内容  
        if '.csv' in table_name:  
            table_name = table_name.split('.csv')[0] 

        # 将 DataFrame 存入 SQLite 数据库
        df.to_sql(table_name, conn, index=False, if_exists='replace')  
    
    # 执行 SQL 查询  
    try:
        result = pd.DataFrame()
        result = pd.read_sql_query(query, conn)  
    except Exception as e:  
        # This will catch any other exception  
        print(f"An error occurred: {e}")  
    finally:
        conn.close()  
        # 输出查询结果  
        print(result)  
        return result
        # 关闭数据库连接 


def main():
    mcp.run()


if __name__ == "__main__":
    main()
