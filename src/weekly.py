import os
import re
from datetime import datetime, timedelta
from data_fetcher import fetch_all_data
from predictor import call_deepseek_custom
from feishu_notifier import send_text
from bitable_writer import (
    get_tenant_access_token,
    query_daily_records_by_date_range,
    find_weekly_record_by_week,
    update_weekly_actual
)


def get_week_range():
    """获取上周（周一至周日）的日期范围"""
    today = datetime.now()
    this_monday = today - timedelta(days=today.weekday())
    last_monday = this_monday - timedelta(days=7)
    last_sunday = last_monday + timedelta(days=6)
    return last_monday, last_sunday


def calculate_weekly_actual(app_token, table_id, token, start_date, end_date):
    """从每日预测表查询上周实际数据，计算均价/最高/最低"""
    records = query_daily_records_by_date_range(
        app_token, table_id, token,
        start_date.strftime("%Y-%m-%d"),
        end_date.strftime("%Y-%m-%d")
    )
    
    prices = []
    for record in records:
        fields = record.get("fields", {})
        price = fields.get("实际价格")
        if price and isinstance(price, (int, float)):
            prices.append(price)
    
    if not prices:
        print("⚠️ 上周无实际价格数据，无法回填")
        return None, None, None
    
    avg_price = round(sum(prices) / len(prices), 1)
    high_price = max(prices)
    low_price = min(prices)
    
    print(f"📊 上周实际数据: 均价={avg_price}, 最高={high_price}, 最低={low_price}, 样本数={len(prices)}")
    return avg_price, high_price, low_price


def main():
    webhook = os.environ.get("FEISHU_WEBHOOK")
    api_key = os.environ.get("DEEPSEEK_API_KEY")
    app_token = os.environ.get("BITABLE_APP_TOKEN")
    daily_table_id = os.environ.get("BITABLE_TABLE_ID")
    weekly_table_id = os.environ.get("WEEKLY_TABLE_ID")
    app_id = os.environ.get("FEISHU_APP_ID")
    app_secret = os.environ.get("FEISHU_APP_SECRET")

    if not all([webhook, api_key, app_token, daily_table_id, weekly_table_id, app_id, app_secret]):
        print("❌ 缺少环境变量")
        return

    # 1. 获取上周日期范围
    start, end = get_week_range()
    week_range = f"{start.strftime('%Y-%m-%d')} ~ {end.strftime('%Y-%m-%d')}"
    print(f"📅 上周: {week_range}")

    # 2. 获取上周实际数据（从每日预测表查询并回填）
    token = get_tenant_access_token(app_id, app_secret)
    avg_price, high_price, low_price = calculate_weekly_actual(
        app_token, daily_table_id, token, start, end
    )

    if avg_price is not None:
        record_id = find_weekly_record_by_week(app_token, weekly_table_id, token, week_range)
        if record_id:
            update_weekly_actual(app_token, weekly_table_id, token, record_id, avg_price, high_price, low_price)
            print(f"✅ 已回填上周实际数据: 均价{avg_price}元/吨")
        else:
            print(f"⚠️ 未找到周次为 '{week_range}' 的记录，请先生成周报")

    # 3. 今日数据（用于本周预测）
    today_data = fetch_all_data()

    # 4. 构造Prompt并生成周报
    prompt = f"""请生成煤炭周度行情报告。

【上周回顾】{week_range}
- 上周均价：{avg_price if avg_price else '待回填'}元/吨
- 上周最高：{high_price if high_price else '待回填'}元/吨
- 上周最低：{low_price if low_price else '待回填'}元/吨

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

    report = call_deepseek_custom(prompt, api_key)
    send_text(webhook, f"📈 煤炭周报\n\n{report}")
    print("✅ 周报完成")


if __name__ == "__main__":
    main()
