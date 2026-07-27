import requests

def send_prediction_card(webhook, prediction):
    """发送每日预测卡片到飞书群"""
    card = {
        "msg_type": "interactive",
        "card": {
            "config": {"wide_screen_mode": True},
            "header": {
                "title": {"tag": "plain_text", "content": "📊 明日长江口5000K价格预测"},
                "template": "blue"
            },
            "elements": [
                {
                    "tag": "div",
                    "text": {
                        "tag": "lark_md",
                        "content": f"""**预测覆盖日期：** {prediction.get('date', '')}
**预测区间：** {prediction.get('lower', '')} - {prediction.get('upper', '')} 元/吨
**涨跌方向：** {prediction.get('direction', '')}
**置信度：** {prediction.get('confidence', '')}

**市场阶段：** {prediction.get('market_stage', '')}
**库存状态：** {prediction.get('inventory_status', '')}
**运费周变化：** {prediction.get('freight_change', '')}%

**操作建议：** {prediction.get('suggestion', '')}

**上行风险：** {prediction.get('up_risk', '')}
**下行风险：** {prediction.get('down_risk', '')}"""
                    }
                },
                {
                    "tag": "note",
                    "elements": [
                        {"tag": "plain_text", "content": "数据来源：CCTD/煤炭资源网 | 预测仅供参考"}
                    ]
                }
            ]
        }
    }
    resp = requests.post(webhook, json=card)
    return resp.status_code == 200


def send_backfill_card(webhook, record):
    """发送回填验证结果卡片"""
    fields = record.get("fields", {})
    card = {
        "msg_type": "interactive",
        "card": {
            "config": {"wide_screen_mode": True},
            "header": {
                "title": {"tag": "plain_text", "content": "✅ 昨日预测验证结果"},
                "template": "green"
            },
            "elements": [
                {
                    "tag": "div",
                    "text": {
                        "tag": "lark_md",
                        "content": f"""**预测覆盖日期：** {fields.get('预测覆盖日期', '')}
**预测区间：** {fields.get('AI预测下限', 0)} - {fields.get('AI预测上限', 0)} 元/吨
**实际价格：** {fields.get('实际价格', 0)} 元/吨
**偏差：** {fields.get('预测偏差', 0)} 元/吨
**准确度：** {fields.get('准确度评估', '')}"""
                    }
                }
            ]
        }
    }
    resp = requests.post(webhook, json=card)
    return resp.status_code == 200


def send_alert_card(webhook, record):
    """发送偏差预警卡片"""
    fields = record.get("fields", {})
    deviation = fields.get('预测偏差', 0)
    card = {
        "msg_type": "interactive",
        "card": {
            "config": {"wide_screen_mode": True},
            "header": {
                "title": {"tag": "plain_text", "content": "⚠️ 预测偏差预警"},
                "template": "red"
            },
            "elements": [
                {
                    "tag": "div",
                    "text": {
                        "tag": "lark_md",
                        "content": f"""**预测覆盖日期：** {fields.get('预测覆盖日期', '')}
**AI预测中间值：** {fields.get('AI预测中间值', 0)} 元/吨
**实际价格：** {fields.get('实际价格', 0)} 元/吨
**偏差：** {deviation} 元/吨
**准确度：** {fields.get('准确度评估', '')}

**偏差归因：** {fields.get('偏差归因', '待分析')}

**建议操作：**
1. 检查当日数据源是否异常
2. 分析偏差原因
3. 如需调整，修改 Prompt 或规则参数后提交代码"""
                    }
                },
                {
                    "tag": "note",
                    "elements": [
                        {"tag": "plain_text", "content": "请分析偏差原因，决定是否优化系统"}
                    ]
                }
            ]
        }
    }
    resp = requests.post(webhook, json=card)
    return resp.status_code == 200


def send_text(webhook, content):
    """发送纯文本消息到飞书群（用于周报/月报）"""
    payload = {
        "msg_type": "text",
        "content": {"text": content}
    }
    resp = requests.post(webhook, json=payload)
    return resp.status_code == 200
