import os
from datetime import datetime
from data_fetcher import fetch_all_data
from predictor import call_deepseek_custom
from feishu_notifier import send_text


def fetch_monthly_actual_data():
    """从多维表格获取上月实际数据（待实现）"""
    return {
        "avg": 792,
        "high": 810,
        "low": 780,
        "change": -15
    }


def main():
    webhook = os.environ.get("FEISHU_WEBHOOK")
    api_key = os.environ.get("DEEPSEEK_API_KEY")

    if not all([webhook, api_key]):
        print("❌ 缺少环境变量")
        return

    monthly_data = fetch_monthly_actual_data()
    today_data = fetch_all_data()

    prompt = f"""请生成煤炭月度行情报告。

【上月回顾】
- 上月均价：{monthly_data['avg']}元/吨
- 上月最高：{monthly_data['high']}元/吨
- 上月最低：{monthly_data['low']}元/吨
- 上月涨跌：{monthly_data['change']}元/吨

【当前数据】
- 长江口5000K：{today_data['yangtze']}元/吨
- 北方三港库存：{today_data['inventory']}万吨
- 海运费：{today_data['freight']}元/吨

【输出格式】
上月行情回顾：...
本月价格中枢预测：...
本月核心驱动逻辑：...
本月采购策略建议：...
"""

    report = call_deepseek_custom(prompt, api_key)
    send_text(webhook, f"📅 煤炭月报\n{report}")

    print("✅ 月报完成")


if __name__ == "__main__":
    main()
