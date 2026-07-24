import os
from bitable_writer import (
    get_tenant_access_token,
    get_latest_record,
    update_actual_price
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
        return

    token = get_tenant_access_token(app_id, app_secret)

    print("📡 获取最新预测记录...")
    record = get_latest_record(app_token, table_id, token)
    if not record:
        print("❌ 无记录可回填")
        return

    print("📡 获取昨日实际价格...")
    actual = fetch_actual_price()
    if not actual:
        print("❌ 无法获取实际价格")
        return

    print(f"📝 回填实际价格: {actual} 元/吨")
    update_actual_price(app_token, table_id, token, record["record_id"], actual)

    print("📤 推送验证结果...")
    send_backfill_card(webhook, record)

    print("✅ 回填完成")


if __name__ == "__main__":
    main()
