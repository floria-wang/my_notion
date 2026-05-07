import os
import sys
import json
import re
from notion_client import Client

# 1. 环境参数读取
NOTION_TOKEN = os.environ.get("NOTION_TOKEN")
DATABASE_ID = os.environ.get("NOTION_DATABASE_ID")

if not NOTION_TOKEN or not DATABASE_ID:
    print("错误: 请检查 GitHub Secrets 是否配置了 NOTION_TOKEN 和 NOTION_DATABASE_ID")
    sys.exit(1)

# 初始化机器人
notion = Client(auth=NOTION_TOKEN)

def get_heatmap_data():
    print(f"--- 正在开启全量扫描模式 (包含自动翻页) ---")
    counts = {} 
    has_more = True
    next_cursor = None
    all_pages = []

    try:
        # --- 核心改进：自动翻页抓取全部数据 ---
        while has_more:
            response = notion.databases.query(
                database_id=DATABASE_ID,
                start_cursor=next_cursor
            )
            all_pages.extend(response.get("results", []))
            has_more = response.get("has_more")
            next_cursor = response.get("next_cursor")
        
        print(f"成功拉取全部数据，共计 {len(all_pages)} 条记录。开始分析...")

        for page in all_pages:
            p = page.get("properties", {})
            
            # --- 核心逻辑 1：增强版状态解析 ---
            # 兼容列名为“状态”的多种类型 (Status, Select)
            status_prop = p.get("状态", {})
            p_type = status_prop.get("type")
            status_name = ""
            
            if p_type == "status":
                status_name = status_prop.get("status", {}).get("name", "")
            elif p_type == "select":
                status_name = status_prop.get("select", {}).get("name", "")
            
            # --- 核心逻辑 2：提取日期并计数 ---
            if status_name == "已完成":
                date_prop = p.get("完成日期", {})
                date_obj = date_prop.get("date") if date_prop else None
                
                if date_obj and date_obj.get("start"):
                    d_str = date_obj.get("start")[:10]
                    counts[d_str] = counts.get(d_str, 0) + 1
        
        # 转换格式
        formatted_data = [[d, c] for d, c in counts.items()]
        # 按日期排序，让 HTML 里的数据更有序
        formatted_data.sort(key=lambda x: x[0])
        
        print(f"统计成功：共点亮 {len(formatted_data)} 天的格格。")
        return formatted_data

    except Exception as e:
        print(f"抓取失败，报错信息: {e}")
        sys.exit(1)

def sync_to_html(data):
    """将数据写入 index.html"""
    file_path = "index.html"
    if not os.path.exists(file_path):
        print(f"错误: 找不到 {file_path}")
        return

    try:
        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()
        
        # 精确匹配标记
        pattern = r"// DATA_START.*?// DATA_END"
        replacement = f"// DATA_START\n        const mockData = {json.dumps(data)};\n        // DATA_END"
        
        new_content = re.sub(pattern, replacement, content, flags=re.DOTALL)
        
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(new_content)
        print(f"--- 成功同步到 index.html ---")
    except Exception as e:
        print(f"写入文件出错: {e}")

if __name__ == "__main__":
    heatmap_data = get_heatmap_data()
    sync_to_html(heatmap_data)
