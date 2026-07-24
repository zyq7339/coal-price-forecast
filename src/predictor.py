import requests
import re
from datetime import datetime


def call_deepseek(data, api_key):
    """调用 DeepSeek API 生成预测报告"""
    url = "https://api.deepseek.com/v1/chat/completions"

    inventory = data.get('inventory', 0)
    if inventory > 2600:
        market_note = "极值看空阶段（库存>2600万吨，供应端利多失效）"
    elif inventory > 2500:
        market_note = "高位震荡阶段（库存>2500万吨，价格承压）"
    else:
        market_note = "正常波动阶段"

    prompt = f"""请根据以下今日数据，预测明日长江口5000K动力煤价格。

【今日日期】{data['today']}
【今日长江口参考价】{data['yangtze']}元/吨
【北方港口CCTD】{data['cctd']}元/吨
【海运费】{data['freight']}元/吨
【北方三港库存】{data['inventory']}万吨
【六大电厂库存/日耗】{data['power']['inventory']}万吨 / {data['power']['consumption']}万吨

【市场判断】{market_note}

【规则】库存>2600万吨时看空。正常波动±1-2元/吨。预测区间以{data['yangtze']}元/吨为中心。

【严格按以下格式输出，不要添加额外文字】
预测覆盖日期：YYYY-MM-DD
AI预测下限：数字
AI预测上限：数字
置信度：高/中/低
市场阶段判断：文字
库存状态：文字
运费周变化：+数字% 或 -数字%
涨跌方向及幅度：上涨/下跌/持平，预计幅度 ±X元/吨
操作建议：文字
上行风险：文字
下行风险：文字
"""

    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {api_key}"
    }
    payload = {
        "model": "deepseek-chat",
        "messages": [{"role": "user", "content": prompt}],
        "temperature": 0.3
    }

    resp = requests.post(url, headers=headers, json=payload)
    return resp.json()["choices"][0]["message"]["content"]


def parse_prediction(text):
    """从 AI 返回的文本中提取结构化数据（增强容错版）"""
    result = {}

    # 清洗文本：移除 Markdown 加粗符号
    text = text.replace('**', '').replace('*', '').replace('__', '')

    # 方法1：标准格式匹配
    patterns = {
        "date": r"预测覆盖日期[：:]\s*(\d{4}-\d{2}-\d{2})",
        "lower": r"AI预测下限[：:]\s*(\d+)",
        "upper": r"AI预测上限[：:]\s*(\d+)",
        "confidence": r"置信度[：:]\s*(高|中|低)",
        "market_stage": r"市场阶段判断[：:]\s*(.+)",
        "inventory_status": r"库存状态[：:]\s*(.+)",
        "freight_change": r"运费周变化[：:]\s*([+-]?\d+)%",
        "direction": r"涨跌方向及幅度[：:]\s*(.+)",
        "suggestion": r"操作建议[：:]\s*(.+)",
        "up_risk": r"上行风险[：:]\s*(.+)",
        "down_risk": r"下行风险[：:]\s*(.+)"
    }

    for key, pattern in patterns.items():
        match = re.search(pattern, text)
        if match:
            result[key] = match.group(1).strip()
        else:
            result[key] = ""

    # 方法2：如果预测区间没匹配到，尝试从文本中智能提取
    if not result.get("lower") or not result.get("upper"):
        range_patterns = [
            r"预测区间[：:]\s*(\d+)\s*[-~]\s*(\d+)",
            r"(\d+)\s*[-~]\s*(\d+)\s*元",
            r"(\d+)\s*-\s*(\d+)\s*元"
        ]
        for pattern in range_patterns:
            match = re.search(pattern, text)
            if match:
                result["lower"] = match.group(1)
                result["upper"] = match.group(2)
                break

    # 方法3：如果还没匹配到，尝试从"预测区间"或"区间"字段提取
    if not result.get("lower") or not result.get("upper"):
        match = re.search(r"(\d+)\s*[-~]\s*(\d+)", text)
        if match:
            result["lower"] = match.group(1)
            result["upper"] = match.group(2)

    # 默认值
    if not result.get("confidence"):
        result["confidence"] = "中"
    if not result.get("freight_change"):
        result["freight_change"] = "0"
    if not result.get("date"):
        result["date"] = datetime.now().strftime("%Y-%m-%d")

    return result
