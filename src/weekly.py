import os
from datetime import datetime, timedelta
from data_fetcher import fetch_all_data
from predictor import call_deepseek_custom
from feishu_notifier import send_text


def get_week_range():
    """获取上周（周一至周日）的日期范围"""
    today = datetime.now()
    this_monday = today - timedelta(days=today.weekday())
    last_monday = this_monday - timedelta(days=7)
    last_sunday = last_monday + timedelta(days=6)
    return last_monday, last_sunday


def fetch_weekly_actual_data():
    """从多维表格获取上周的实际数据（待实现）"""
    # TODO: 调用多维表格API查询上周记录
    return {
        "avg": 795,
        "high": 800,
        "low": 788,
        "change": -5
    }


def main():
    webhook = os.environ.get("FEISHU_WEBHOOK")
    api_key = os.environ.get("DEEPSEEK_API_KEY")

    if not all([webhook, api_key]):
        print("❌ 缺少环境变量")
        return

    # 1. 上周回顾数据
    start, end = get_week_range()
    weekly_data = fetch_weekly_actual_data()

    # 2. 今日数据（用于本周预测）
    today_data = fetch_all_data()

    # 3. 构造 Prompt
    prompt = f"""请生成煤炭周度行情报告。

【上周回顾】{start.strftime('%Y-%m-%d')} ~ {end.strftime('%Y-%m-%d')}
- 上周均价：{weekly_data['avg']}元/吨
- 上周最高：{weekly_data['high']}元/吨
- 上周最低：{weekly_data['low']}元/吨
- 上周涨跌：{weekly_data['change']}元/吨

【当前数据】
- 长江口5000K：{today_data['yangtze']}元/吨
- 北方三港库存：{today_data['inventory']}万吨
- 海运费：{today_data['freight']}元/吨
- 六大电厂库存：{today_data['power']['inventory']}万吨
- 六大电厂日耗：{today_data['power']['consumption']}万吨

【输出格式】
上周行情回顾：
- 开盘：XXX
- 最高：XXX
- 最低：XXX
- 收盘：XXX
- 涨跌：±X

本周走势预测：
- 预测区间：XXX-XXX
- 整体判断：上涨/震荡/下跌
- 核心驱动因素：1.XXX 2.XXX 3.XXX

操作建议：XXX
风险提示：XXX
"""

    # 4. 调用AI
    report = call_deepseek_custom(prompt, api_key)

    # 5. 推送纯文本消息（周报）
    send_text(webhook, f"📈 煤炭周报\n{report}")

    print("✅ 周报完成")


if __name__ == "__main__":
    main()
