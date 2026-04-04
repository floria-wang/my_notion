import os
import json
import re
from notion_client import Client

# 1. 初始化 Notion 客户端
# 确保 GitHub Secrets 中已配置 NOTION_TOKEN
notion = Client(auth=os.environ["NOTION_TOKEN"])
database_id = os.environ["NOTION_DATABASE_ID"]

def get_notion_data():
    """从 Notion 数据库抓取所有『状态』为『已完成』的任务"""
    all_results = []
    has_more = True
    start_cursor = None
    
    print("--- 开始从 Notion 抓取数据 ---")
    
    while has_more:
        try:
            # 极简调用：如果 notion.databases.query 报错，说明库结构有变
            # 我们直接使用客户端内置的 request 方法或最稳健的路径
            response = notion.databases.query(
                **{
                    "database_id": database_id,
                    "start_cursor": start_cursor,
                    "filter": {
                        "property": "状态",
                        "status": {"equals": "已完成"}
                    }
                }
            )
            # 如果上面还是报错，请尝试将调用改为：notion.request(path=f"databases/{database_id}/query", method="POST", body=...)
            # 但 3.0 版本理论上应该支持 notion.databases.query
            
            all_results.extend(response.get("results", []))
            has_more = response.get("has_more", False)
            start_cursor = response.get("next_cursor")
            print(f"当前已抓取 {len(all_results)} 条记录...")
            
        except Exception as e:
            # 打印出 notion 对象的所有属性，方便我们精准 Debug
            print(f"DEBUG: notion 对象拥有的属性: {dir(notion)}")
            print(f"DEBUG: notion.databases 拥有的属性: {dir(notion.databases)}")
            raise e


def sync_to_html(data):
    """将数据写入 index.html"""
    file_path = "index.html"
    if not os.path.exists(file_path):
        print(f"错误: 找不到 {file_path} 文件")
        return

    with open(file_path, "r", encoding="utf-8") as f:
        content = f.read()
    
    # 正则替换逻辑
    pattern = r"// DATA_START.*?// DATA_END"
    replacement = f"// DATA_START\n        const mockData = {json.dumps(data)};\n        // DATA_END"
    
    new_content = re.sub(pattern, replacement, content, flags=re.DOTALL)
    
    with open(file_path, "w", encoding="utf-8") as f:
        f.write(new_content)
    print("--- 成功同步到 index.html ---")

if __name__ == "__main__":
    try:
        data = get_notion_data()
        sync_to_html(data)
    except Exception as e:
        print(f"【系统崩溃】详细错误信息: {e}")
        exit(1)