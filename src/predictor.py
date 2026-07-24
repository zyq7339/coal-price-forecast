prompt = f"""请根据以下今日数据，生成明日（{data['today']}的明天）长江口5000K动力煤价格预测报告。

【今日日期】
{data['today']}

【今日数据】
- CCTD 5000K价格：{data['cctd']}元/吨（北方港口）
- CCI5000指数：{data['cci']}元/吨（北方港口）
- 海运费（秦皇岛→张家港4-5万吨）：{data['freight']}元/吨
- 北方三港库存：{data['inventory']}万吨
- 六大电厂库存：{data['power']['inventory']}万吨
- 六大电厂日耗：{data['power']['consumption']}万吨

【业务规则】
- 正常单日波动：±1-2元/吨；异常波动阈值：>±5元/吨（需预警）
- 北方三港库存高位：>2500万吨；极值看空：>2600万吨（供应端利多失效）
- 北方→长江口正常价差：50-60元/吨
- 长江口价格 ≈ 北方港口价格 + 海运费 + 其他费用（约50-60元价差）
- 海运费单周涨跌>15%时，涨跌放大系数1.5倍

【当前市场判断参考】
- 目前北方三港库存{data['inventory']}万吨，已{'触发极值看空（>2600万吨）' if data['inventory'] > 2600 else '处于高位区间'}
- 请根据库存数据判断市场阶段，库存>2600时必须判定为"极值看空阶段"

【输出格式要求】
严格按照以下格式输出，不要添加额外内容：

预测覆盖日期：YYYY-MM-DD（今日之后的第一个工作日）
AI预测下限：XXX（长江口5000K价格）
AI预测上限：XXX（长江口5000K价格）
置信度：高/中/低
市场阶段判断：极值看空阶段 / 高位震荡阶段 / 筑底企稳阶段 / 旺季反弹阶段
库存状态：北方三港XXX万吨（高位/极值），六大电厂XXX万吨（高位/正常）
运费周变化：+X% 或 -X%
偏差归因：待回填验证
涨跌方向及幅度：上涨/下跌/持平，预计幅度 ±X元/吨
操作建议：XXX
上行风险：XXX
下行风险：XXX

【历史教训自查】
是否受季节性思维影响：是/否
是否考虑库存极值：是/否
是否考虑运费传导：是/否
"""


### 修复3：`src/predictor.py` — 修改解析逻辑，增加运费变化字段的默认值

在 `parse_prediction` 函数中，确保 `freight_change` 有默认值：

```python
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
            # 为关键字段设置默认值
            if key == "freight_change":
                result[key] = "0"  # 默认为0
            elif key == "date":
                result[key] = datetime.now().strftime("%Y-%m-%d")  # 默认今天
            else:
                result[key] = ""
    
    return result
