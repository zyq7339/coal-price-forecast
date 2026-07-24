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

【核心参考数据】
- 今日长江口5000K实际价格：{data['yangtze']}元/吨（以此为基准预测明日）
- 北方港口CCTD 5000K：{data['cctd']}元/吨
- 北方港口CCI5000：{data['cci']}元/吨
- 海运费：{data['freight']}元/吨
- 北方三港库存：{data['inventory']}万吨
- 六大电厂库存：{data['power']['inventory']}万吨
- 六大电厂日耗：{data['power']['consumption']}万吨

【市场判断】
{market_note}

【业务规则】
- 正常单日波动：±1-2元/吨；异常波动阈值：>±5元/吨
- 库存>2600万吨时，价格应偏弱运行
- 预测区间应以今日长江口价格 {data['yangtze']} 元/吨为中心，上下浮动
- 北方→长江口价差约50-60元/吨

【输出格式】
预测覆盖日期：YYYY-MM-DD
AI预测下限：XXX
AI预测上限：XXX
置信度：高/中/低
市场阶段判断：XXX
库存状态：XXX
运费周变化：+X% 或 -X%
涨跌方向及幅度：上涨/下跌/持平，预计幅度 ±X元/吨
操作建议：XXX
上行风险：XXX
下行风险：XXX

【历史教训自查】
是否受季节性思维影响：是/否
是否考虑库存极值：是/否
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
    """从 AI 返回的文本中提取结构化数据"""
    result = {}

    # 清洗文本：移除 Markdown 加粗符号
    text = text.replace('**', '').replace('*', '').replace('__', '')

    patterns = {
        "date": r"预测覆盖日期：(\d{4}-\d{2}-\d{2})",
        "lower": r"AI预测下限：(\d+)",
        "upper": r"AI预测上限：(\d+)",
        "confidence": r"置信度：(高|中|低)",
        "market_stage": r"市场阶段判断：(.+)",
        "inventory_status": r"库存状态：(.+)",
        "freight_change": r"运费周变化：([+-]?\d+)%",
        "direction": r"涨跌方向及幅度：(.+)",
        "suggestion": r"操作建议：(.+)",
        "up_risk": r"上行风险：(.+)",
        "down_risk": r"下行风险：(.+)"
    }

    for key, pattern in patterns.items():
        match = re.search(pattern, text)
        if match:
            result[key] = match.group(1).strip()
        else:
            if key == "freight_change":
                result[key] = "0"
            elif key == "date":
                result[key] = datetime.now().strftime("%Y-%m-%d")
            else:
                result[key] = ""

    return result
