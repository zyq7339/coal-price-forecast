import os
import requests
from datetime import datetime, timedelta
from data_fetcher import fetch_all_data
from predictor import call_deepseek, parse_prediction
from feishu_notifier import send_prediction_card
from bitable_writer import write_prediction, get_tenant_access_token


def get_week_range():
    """获取上周（周一至周日）的日期范围"""
    today = datetime.now()
    # 本周一
    this_monday = today - timedelta(days=today.weekday())
    # 上周一
    last_monday = this_monday - timedelta(days=7)
    # 上周日
    last_sunday = last_monday + timedelta(days=6)
    return last_monday, last_sunday


def fetch_weekly_actual_data():
    """从多维表格获取上周的实际数据"""
    # TODO: 调用多维表格API，查询上周所有每日记录
    # 计算：上周均价、最高价、最低价
    return {
        "avg": 795,    # 示例值
        "high": 800,   # 示例值
        "low": 788,    # 示例值
        "change": -5   # 示例值
    }


def main():
    webhook = os.environ.get("FEISHU_WEBHOOK")
    api_key = os.environ.get("DEEPSEEK_API_KEY")
    app_token = os.environ.get("BITABLE_APP_TOKEN")
    table_id = os.environ.get("BITABLE_TABLE_ID")
    app_id = os.environ.get("FEISHU_APP_ID")
    app_secret = os.environ.get("FEISHU_APP_SECRET")

    if not all([webhook, api_key]):
        print("❌ 缺少环境变量")
        return

    # 1. 获取上周日期范围
    start, end = get_week_range()
    print(f"📅 上周回顾: {start.strftime('%Y-%m-%d')} ~ {end.strftime('%Y-%m-%d')}")

    # 2. 获取上周实际数据
    weekly_data = fetch_weekly_actual_data()
    print(f"📊 上周均价: {weekly_data['avg']}元/吨")

    # 3. 获取今日数据用于本周预测
    today_data = fetch_all_data()

    # 4. 调用AI生成周报
    prompt = f"""请生成每周煤炭行情预测报告。

【上周回顾】
- 上周均价: {weekly_data['avg']}元/吨
- 上周最高: {weekly_data['high']}元/吨
- 上周最低: {weekly_data['low']}元/吨
- 上周涨跌: {weekly_data['change']}元/吨

【当前数据】
- 长江口5000K: {today_data['yangtze']}元/吨
- 北方三港库存: {today_data['inventory']}万吨
- 海运费: {today_data['freight']}元/吨

【输出格式】
上周行情回顾：
- 开盘：XXX元/吨
- 最高：XXX元/吨
- 最低：XXX元/吨
- 收盘：XXX元/吨
- 涨跌：±X元/吨

本周走势预测：
- 预测区间：XXX-XXX元/吨
- 整体判断：上涨/震荡/下跌
- 核心驱动因素：1.XXX 2.XXX 3.XXX

操作建议：XXX
风险提示：XXX
"""
    # 调用AI并推送
    report = call_deepseek({"prompt": prompt, "today": datetime.now().strftime("%Y-%m-%d")}, api_key)
    send_prediction_card(webhook, {"date": datetime.now().strftime("%Y-%m-%d"), "report": report})

    print("✅ 周报完成")


if __name__ == "__main__":
    main()
