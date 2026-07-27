import os
import re
from datetime import datetime, timedelta
from calendar import monthrange
from data_fetcher import fetch_all_data
from predictor import call_deepseek_custom
from feishu_notifier import send_text
from bitable_writer import (
    get_tenant_access_token,
    query_daily_records_by_date_range,
    find_monthly_record_by_month,
    update_monthly_actual
)


def get_month_range():
    """获取上月（月初至月末）的日期范围"""
    today = datetime.now()
    if today.month == 1:
        year = today.year - 1
        month = 12
    else:
        year = today.year
        month = today.month - 1
    
    first_day = datetime(year, month, 1)
    last_day = datetime(year, month, monthrange(year, month)[1])
    return first_day, last_day


def calculate_monthly_actual(app_token, table_id, token, start_date, end_date):
    """从每日预测表查询上月实际数据，计算均价/最高/最低"""
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
        print("⚠️ 上月无实际价格数据，无法回填")
        return None, None, None
    
    avg_price = round(sum(prices) / len(prices), 1)
    high_price = max(prices)
    low_price = min(prices)
    
    print(f"📊 上月实际数据: 均价={avg_price}, 最高={high_price}, 最低={low_price}, 样本数={len(prices)}")
    return avg_price, high_price, low_price


def main():
    webhook = os.environ.get("FEISHU_WEBHOOK")
    api_key = os.environ.get("DEEPSEEK_API_KEY")
    app_token = os.environ.get("BITABLE_APP_TOKEN")
    daily_table_id = os.environ.get("BITABLE_TABLE_ID")
    monthly_table_id = os.environ.get("MONTHLY_TABLE_ID")
    app_id = os.environ.get("FEISHU_APP_ID")
    app_secret = os.environ.get("FEISHU_APP_SECRET")

    if not all([webhook, api_key, app_token, daily_table_id, monthly_table_id, app_id, app_secret]):
        print("❌ 缺少环境变量")
        return

    # 1. 获取上月日期范围
    start, end = get_month_range()
    month_label = start.strftime("%Y年%m月")
    print(f"📅 上月: {month_label} ({start.strftime('%Y-%m-%d')} ~ {end.strftime('%Y-%m-%d')})")

    # 2. 获取上月实际数据（从每日预测表查询并回填）
    token = get_tenant_access_token(app_id, app_secret)
    avg_price, high_price, low_price = calculate_monthly_actual(
        app_token, daily_table_id, token, start, end
    )

    if avg_price is not None:
        record_id = find_monthly_record_by_month(app_token, monthly_table_id, token, month_label)
        if record_id:
            update_monthly_actual(app_token, monthly_table_id, token, record_id, avg_price, high_price, low_price)
            print(f"✅ 已回填上月实际数据: 均价{avg_price}元/吨")
        else:
            print(f"⚠️ 未找到月份为 '{month_label}' 的记录，请先生成月报")

    # 3. 今日数据
    today_data = fetch_all_data()

    # 4. 构造Prompt并生成月报
    prompt = f"""请生成煤炭月度行情报告。

【上月回顾】{month_label}
- 上月均价：{avg_price if avg_price else '待回填'}元/吨
- 上月最高：{high_price if high_price else '待回填'}元/吨
- 上月最低：{low_price if low_price else '待回填'}元/吨

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
    send_text(webhook, f"📅 煤炭月报\n\n{report}")
    print("✅ 月报完成")


if __name__ == "__main__":
    main()
