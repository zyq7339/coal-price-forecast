import os
from bitable_writer import get_tenant_access_token, get_latest_record
from feishu_notifier import send_alert_card


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

    record = get_latest_record(app_token, table_id, token)
    if not record:
        print("❌ 无记录")
        return

    fields = record.get("fields", {})
    deviation = fields.get("预测偏差", 0)

    if abs(deviation) > 15:
        send_alert_card(webhook, record)
        print(f"⚠️ 预警已发送，偏差：{deviation} 元/吨")
    else:
        print(f"✅ 偏差 {deviation} 在正常范围内（≤15 元/吨）")


if __name__ == "__main__":
    main()
