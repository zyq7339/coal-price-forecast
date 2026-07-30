import os
import requests
from datetime import datetime, timedelta
from bitable_writer import (
    get_tenant_access_token,
    get_latest_record,
    update_actual_price,
    find_record_by_date,
    update_freight_change
)
from feishu_notifier import send_backfill_card
from data_fetcher import fetch_actual_price


def main():
    webhook = os.environ.get("FEISHU_WEBHOOK")
    app_token = os.environ.get("BITABLE_APP_TOKEN")
    table_id = os.environ.get("BITABLE_TABLE_ID")
    app_id = os.environ.get("FEISHU_APP_ID")
    app_secret = os.environ.get("FEISHU_APP_SECRET")

    if not all([webhook, app_token, table_id, app_id, app_secret]):
        print("❌ 缺少环境变量")
        print(f"   FEISHU_WEBHOOK: {'已设置' if webhook else '缺失'}")
        print(f"   BITABLE_APP_TOKEN: {'已设置' if app_token else '缺失'}")
        print(f"   BITABLE_TABLE_ID: {'已设置' if table_id else '缺失'}")
        print(f"   FEISHU_APP_ID: {'已设置' if app_id else '缺失'}")
        print(f"   FEISHU_APP_SECRET: {'已设置' if app_secret else '缺失'}")
        return

    token = get_tenant_access_token(app_id, app_secret)
    if not token:
        print("❌ 获取 Token 失败")
        return

    print("📡 获取最新预测记录...")
    record = get_latest_record(app_token, table_id, token)
    if not record:
        print("❌ 无记录可回填")
        return

    fields = record.get("fields", {})
    record_id = record["record_id"]
    current_date = fields.get("预测覆盖日期")
    print(f"📋 最新记录日期: {current_date}")

    # 1. 回填实际价格
    actual = fetch_actual_price()
    if actual:
        print(f"📝 回填实际价格: {actual} 元/吨")
        update_actual_price(app_token, table_id, token, record_id, actual)
        print("✅ 实际价格回填完成")
    else:
        print("⚠️ 无法获取实际价格")

    # 2. 计算并更新运费周变化
    if current_date:
        try:
            date_obj = datetime.strptime(current_date, "%Y-%m-%d")
            last_week_date = (date_obj - timedelta(days=7)).strftime("%Y-%m-%d")
            print(f"🔍 查找上周同期记录: {last_week_date}")

            last_record = find_record_by_date(app_token, table_id, token, last_week_date)
            if last_record:
                last_freight = last_record.get("fields", {}).get("海运费")
                current_freight = fields.get("海运费")
                if last_freight and current_freight and last_freight != 0:
                    change_pct = (current_freight - last_freight) / last_freight * 100
                    change_pct = round(change_pct, 2)
                    print(f"📊 运费周变化: {change_pct}%")
                    update_freight_change(app_token, table_id, token, record_id, change_pct)
                    print("✅ 运费周变化更新完成")
                else:
                    print("⚠️ 缺少运费数据，无法计算周变化")
            else:
                print(f"⚠️ 未找到 {last_week_date} 的记录，无法计算运费周变化")
        except Exception as e:
            print(f"⚠️ 计算运费周变化时出错: {e}")

    # 3. 推送验证结果卡片
    send_backfill_card(webhook, record)
    print("✅ 回填完成")


if __name__ == "__main__":
    main()
