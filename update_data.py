import os
import json
import re
from notion_client import Client

# 1. 初始化 Notion 客户端
# 确保你在 GitHub Secrets 中配置了 NOTION_TOKEN 和 NOTION_DATABASE_ID
notion = Client(auth=os.environ["NOTION_TOKEN"])
database_id = os.environ["NOTION_DATABASE_ID"]

def get_notion_data():
    """从 Notion 数据库抓取所有『状态』为『已完成』的任务"""
    all_results = []
    has_more = True
    start_cursor = None
    
    print("正在从 Notion 抓取数据...")
    
    while has_more:
        response = notion.databases.query(
            database_id=database_id,
            start_cursor=start_cursor,
            filter={
                "property": "状态",
                "status": {"equals": "已完成"}
            }
        )
        all_results.extend(response["results"])
        has_more = response["has_more"]
        start_cursor = response["next_cursor"]

    # 统计每天完成的数量
    counts = {}
    for page in all_results:
        # 提取『完成日期』属性
        properties = page.get("properties", {})
        date_prop = properties.get("完成日期", {}).get("date")
        
        if date_prop and date_prop.get("start"):
            d = date_prop["start"]
            # 只取 YYYY-MM-DD 部分
            d_short = d.split('T')[0]
            counts[d_short] = counts.get(d_short, 0) + 1
    
    # 转换为 ECharts 格式: [[日期, 数量], [日期, 数量]...]
    formatted_data = [[d, c] for d, c in counts.items()]
    print(f"提取完成，共发现 {len(formatted_data)} 天有学习记录。")
    return formatted_data

def sync_to_html(data):
    """将抓取到的数据写入 index.html 的 mockData 标记位置"""
    file_path = "index.html"
    
    if not os.path.exists(file_path):
        print(f"错误: 找不到 {file_path}")
        return

    with open(file_path, "r", encoding="utf-8") as f:
        content = f.read()
    
    # 使用正则表达式替换 DATA_START 和 DATA_END 之间的内容
    pattern = r"// DATA_START.*?// DATA_END"
    replacement = f"// DATA_START\n        const mockData = {json.dumps(data)};\n        // DATA_END"
    
    new_content = re.sub(pattern, replacement, content, flags=re.DOTALL)
    
    with open(file_path, "w", encoding="utf-8") as f:
        f.write(new_content)
    print("成功更新 index.html 中的数据！")

if __name__ == "__main__":
    try:
        data = get_notion_data()
        sync_to_html(data)
    except Exception as e:
        print(f"执行出错: {e}")
        exit(1) # 确保 GitHub Action 能捕获到失败