import requests
import re

def call_deepseek(data, api_key):
    """调用 DeepSeek API 生成预测报告"""
    url = "https://api.deepseek.com/v1/chat/completions"
    
    prompt = f"""请根据以下今日数据，生成明日长江口5000K动力煤价格预测报告。

【今日数据】
- CCTD 5000K价格：{data['cctd']}元/吨
- CCI5000指数：{data['cci']}元/吨
- 海运费（秦皇岛→张家港4-5万吨）：{data['freight']}元/吨
- 北方三港库存：{data['inventory']}万吨
- 六大电厂库存：{data['power']['inventory']}万吨
- 六大电厂日耗：{data['power']['consumption']}万吨

【业务规则】
- 正常单日波动：±1-2元/吨
- 异常波动阈值：>±5元/吨（需预警）
- 北方三港库存高位：>2500万吨
- 北方三港库存极值看空：>2600万吨（供应端利多失效）
- 北方→长江口正常价差：50-60元/吨
- 海运费单周涨跌>15%时，涨跌放大系数1.5倍

【输出格式要求】
严格按照以下格式输出，不要添加额外内容：

预测覆盖日期：YYYY-MM-DD
AI预测下限：XXX
AI预测上限：XXX
置信度：高/中/低
市场阶段判断：XXX
库存状态：XXX
运费周变化：±X%
偏差归因：XXX
涨跌方向及幅度：上涨/下跌/持平，预计幅度 ±X元/吨
操作建议：XXX
上行风险：XXX
下行风险：XXX

【历史教训自查】
是否受季节性思维影响：是/否
是否考虑库存极值：是/否
是否考虑运费传导：是/否
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
    patterns = {
        "date": r"预测覆盖日期：(\d{4}-\d{2}-\d{2})",
        "lower": r"AI预测下限：(\d+)",
        "upper": r"AI预测上限：(\d+)",
        "confidence": r"置信度：(高|中|低)",
        "market_stage": r"市场阶段判断：(.+)",
        "inventory_status": r"库存状态：(.+)",
        "freight_change": r"运费周变化：([+-]?\d+)%",
        "attribution": r"偏差归因：(.+)",
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
            result[key] = ""
    
    return result
