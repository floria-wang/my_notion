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
            # 核心修复点：确保调用路径正确
            response = notion.databases.query(
                database_id=database_id,
                start_cursor=start_cursor,
                filter={
                    "property": "状态",
                    "status": {"equals": "已完成"}
                }
            )
            all_results.extend(response.get("results", []))
            has_more = response.get("has_more", False)
            start_cursor = response.get("next_cursor")
            print(f"当前已抓取 {len(all_results)} 条记录...")
            
        except Exception as e:
            print(f"Notion 查询失败: {e}")
            raise e

    # 2. 统计每天完成的数量
    counts = {}
    for page in all_results:
        properties = page.get("properties", {})
        
        # 提取『完成日期』属性
        date_wrap = properties.get("完成日期", {})
        if date_wrap and date_wrap.get("type") == "date":
            date_prop = date_wrap.get("date")
            if date_prop and date_prop.get("start"):
                d = date_prop["start"].split('T')[0] # 只取日期部分
                counts[d] = counts.get(d, 0) + 1
    
    # 转换为 ECharts 格式: [[日期, 数量], ...]
    formatted_data = [[d, c] for d, c in counts.items()]
    print(f"数据处理完毕：发现 {len(formatted_data)} 天有打卡记录。")
    return formatted_data

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