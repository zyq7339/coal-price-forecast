import requests
import re
from datetime import datetime


def call_deepseek(data, api_key):
    """调用 DeepSeek API 生成明日预测（基于今日收盘 + 多维因子）"""
    url = "https://api.deepseek.com/v1/chat/completions"

    # 构建基础提示词
    prompt = f"""请根据今日（{data['today']}）收盘数据，预测明日（{data['tomorrow']}）长江口5000K动力煤价格。

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
【今日收盘数据】
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

今日长江口5000K收盘参考价：{data['yangtze']} 元/吨
今日北方港口5000K收盘价：{data['cctd']} 元/吨
今日海运费（秦皇岛→张家港）：{data['freight']} 元/吨
今日运费周变化：{data['freight_change']}%（正=上涨，负=下跌）
今日北方三港库存：{data['inventory']} 万吨
今日六大电厂库存：{data['power']['inventory']} 万吨
今日六大电厂日耗：{data['power']['consumption']} 万吨
"""

    if data.get('yangtze_inventory'):
        prompt += f"今日长江口库存：{data['yangtze_inventory']} 万吨\n"

    if data.get('event'):
        prompt += f"\n【市场动态】\n{data['event']}\n"

    prompt += f"""
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
【预测判断维度】
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

请从以下维度综合判断明日涨跌方向及幅度：

1. 库存维度：
   - 北方三港库存 {data['inventory']} 万吨
     * >2600 → 极值看空
     * 2500-2600 → 高位压制
     * 2300-2500 → 中性
     * <2300 → 偏低支撑
   - 长江口库存（如有）：>1400压制，<1200支撑

2. 电厂日耗维度：
   - 当前日耗 {data['power']['consumption']} 万吨
     * >90 → 需求偏强（利多）
     * 80-90 → 中性
     * <80 → 需求偏弱（利空）

3. 运费趋势维度：
   - 周变化 {data['freight_change']}%
     * >+5% → 成本支撑增强（利多）
     * <-5% → 成本支撑减弱（利空）

4. 价格动量维度：
   - 今日收盘 {data['yangtze']} 元/吨
   - 结合近期市场动态，判断今日价格处于近期什么位置
   - 是否存在连续上涨/下跌的惯性

5. 事件驱动维度：
   - 若有封航、暴雨、安检等供给端扰动 → 短期利多
   - 若有政策调控、进口煤冲击等 → 短期利空

6. 综合判断：
   - 综合以上所有因素，判断明日价格方向（上涨/下跌/持平）
   - 并给出合理的价格波动区间

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
【输出格式】
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

预测覆盖日期：{data['tomorrow']}
AI预测下限：XXX（整数）
AI预测上限：XXX（整数）
置信度：高/中/低
市场阶段判断：极值看空/高位震荡/正常波动/需求偏强
库存状态：XXX
运费周变化：±X%
涨跌方向及幅度：上涨/下跌/持平，预计幅度 ±X元/吨
判断依据：综合各维度简要说明（50字以内）
操作建议：XXX
上行风险：XXX
下行风险：XXX
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
    text = text.replace('**', '').replace('*', '').replace('__', '')

    patterns = {
        "date": r"预测覆盖日期[：:]\s*(\d{4}-\d{2}-\d{2})",
        "lower": r"AI预测下限[：:]\s*(\d+)",
        "upper": r"AI预测上限[：:]\s*(\d+)",
        "confidence": r"置信度[：:]\s*(高|中|低)",
        "market_stage": r"市场阶段判断[：:]\s*(.+)",
        "inventory_status": r"库存状态[：:]\s*(.+)",
        "freight_change": r"运费周变化[：:]\s*([+-]?\d+)%",
        "direction": r"涨跌方向及幅度[：:]\s*(.+)",
        "basis": r"判断依据[：:]\s*(.+)",
        "suggestion": r"操作建议[：:]\s*(.+)",
        "up_risk": r"上行风险[：:]\s*(.+)",
        "down_risk": r"下行风险[：:]\s*(.+)"
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


def call_deepseek_custom(prompt_text, api_key):
    """使用自定义 Prompt 调用 DeepSeek API（用于周报/月报）"""
    url = "https://api.deepseek.com/v1/chat/completions"
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {api_key}"
    }
    payload = {
        "model": "deepseek-chat",
        "messages": [{"role": "user", "content": prompt_text}],
        "temperature": 0.3
    }
    resp = requests.post(url, headers=headers, json=payload)
    return resp.json()["choices"][0]["message"]["content"]
