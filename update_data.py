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
    print(f"--- 正在连接 Notion 数据库 [状态] 列 ---")
    counts = {} 
    
    try:
        # 执行查询
        response = notion.databases.query(database_id=DATABASE_ID)
        pages = response.get("results", [])
        
        for page in pages:
            p = page.get("properties", {})
            
            # --- 核心逻辑 1：提取状态列 ---
            # 适配列名为“状态”的 Status 或 Select 类型
            status_obj = p.get("状态", {}).get("status") or p.get("状态", {}).get("select")
            status_name = status_obj.get("name", "") if status_obj else ""
            
            # --- 核心逻辑 2：提取日期并计数 ---
            # 只有当 [状态] 为 “已完成” 时才进行热力图统计
            if status_name == "已完成":
                date_obj = p.get("完成日期", {}).get("date")
                if date_obj and date_obj.get("start"):
                    # 截取日期部分 YYYY-MM-DD
                    d_str = date_obj.get("start")[:10]
                    counts[d_str] = counts.get(d_str, 0) + 1
        
        # 转换格式为 ECharts 绘图所需的 [[日期, 数量], ...]
        formatted_data = [[d, c] for d, c in counts.items()]
        print(f"统计成功：共发现 {len(formatted_data)} 天有“已完成”的学习记录。")
        return formatted_data

    except Exception as e:
        print(f"抓取失败，报错信息: {e}")
        sys.exit(1)

def sync_to_html(data):
    """将数据写入 index.html 的特定注释标记位置"""
    file_path = "index.html"
    if not os.path.exists(file_path):
        print(f"错误: 找不到 {file_path}")
        return

    try:
        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()
        
        # 正则替换：查找 // DATA_START 到 // DATA_END 之间的内容
        pattern = r"// DATA_START.*?// DATA_END"
        replacement = f"// DATA_START\n        const mockData = {json.dumps(data)};\n        // DATA_END"
        
        new_content = re.sub(pattern, replacement, content, flags=re.DOTALL)
        
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(new_content)
        print(f"--- 成功更新 index.html ---")
    except Exception as e:
        print(f"写入文件出错: {e}")

if __name__ == "__main__":
    # 启动工作流
    heatmap_data = get_heatmap_data()
    sync_to_html(heatmap_data)