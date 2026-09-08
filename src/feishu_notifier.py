import requests


def send_prediction_card(webhook, prediction):
    """发送预测卡片到飞书群"""
    card = {
        "msg_type": "interactive",
        "card": {
            "config": {"wide_screen_mode": True},
            "header": {
                "title": {"tag": "plain_text", "content": f"📊 明日（{prediction.get('date', '')}）长江口5000K预测"},
                "template": "blue"
            },
            "elements": [
                {
                    "tag": "div",
                    "text": {
                        "tag": "lark_md",
                        "content": f"""**预测区间**：{prediction.get('lower', '?')} - {prediction.get('upper', '?')} 元/吨
**涨跌方向**：{prediction.get('direction', '')}
**置信度**：{prediction.get('confidence', '')}

**市场阶段**：{prediction.get('market_stage', '')}
**库存状态**：{prediction.get('inventory_status', '')}
**运费周变化**：{prediction.get('freight_change', '0')}%

**判断依据**：{prediction.get('basis', '')}

**操作建议**：{prediction.get('suggestion', '')}

**上行风险**：{prediction.get('up_risk', '')}
**下行风险**：{prediction.get('down_risk', '')}"""
                    }
                },
                {
                    "tag": "note",
                    "elements": [
                        {"tag": "plain_text", "content": "基于今日收盘数据预测 | 仅供参考，实际交易请结合自身情况决策"}
                    ]
                }
            ]
        }
    }
    resp = requests.post(webhook, json=card)
    return resp.status_code == 200


def send_text(webhook, content):
    """发送纯文本消息到飞书群"""
    payload = {
        "msg_type": "text",
        "content": {"text": content}
    }
    resp = requests.post(webhook, json=payload)
    return resp.status_code == 200
