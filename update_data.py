import os
import json
import re
from collections import Counter
from notion_client import Client

# 初始化
notion = Client(auth=os.environ["NOTION_TOKEN"])
database_id = os.environ["NOTION_DATABASE_ID"]

def get_notion_data():
    all_dates = []
    has_more = True
    start_cursor = None
    
    print("--- 开始从 Notion [考研科目] 数据库抓取数据 ---")
    
    while has_more:
        response = notion.databases.query(
            **{
                "database_id": database_id,
                "start_cursor": start_cursor,
                "filter": {
                    "property": "状态",
                    "status": {"equals": "已完成"} # 确保 Notion 中状态切换为“已完成”
                }
            }
        )
        
        for page in response.get("results", []):
            # 提取“完成日期”属性的值
            properties = page.get("properties", {})
            date_info = properties.get("完成日期", {}).get("date")
            
            if date_info and date_info.get("start"):
                all_dates.append(date_info["start"])
        
        has_more = response.get("has_more", False)
        start_cursor = response.get("next_cursor")

    # 统计每天出现的次数，生成 ECharts 要求的格式: [["2026-01-01", 5], ...]
    date_counts = Counter(all_dates)
    formatted_data = [[date, count] for date, count in date_counts.items()]
    return formatted_data

def sync_to_html(data):
    file_path = "index.html"
    if not os.path.exists(file_path):
        return

    with open(file_path, "r", encoding="utf-8") as f:
        content = f.read()
    
    # 将格式化后的数据填入 mockData
    pattern = r"// DATA_START.*?// DATA_END"
    replacement = f"// DATA_START\n        const mockData = {json.dumps(data)};\n        // DATA_END"
    
    new_content = re.sub(pattern, replacement, content, flags=re.DOTALL)
    
    with open(file_path, "w", encoding="utf-8") as f:
        f.write(new_content)
    print(f"--- 成功同步 {len(data)} 天的数据到 index.html ---")

if __name__ == "__main__":
    try:
        data = get_notion_data()
        sync_to_html(data)
    except Exception as e:
        print(f"错误: {e}")
        exit(1)