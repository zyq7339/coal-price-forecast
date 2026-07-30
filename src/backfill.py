import os
import requests
from bitable_writer import get_tenant_access_token, get_latest_record, update_actual_price
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
        # 尝试直接查询记录数量，便于排查
        url = f"https://open.feishu.cn/open-apis/bitable/v1/apps/{app_token}/tables/{table_id}/records"
        headers = {"Authorization": f"Bearer {token}"}
        resp = requests.get(url, headers=headers)
        data = resp.json()
        items = data.get("data", {}).get("items", [])
        print(f"📊 表格中共有 {len(items)} 条记录")
        if items:
            print("📋 第一条记录字段:", list(items[0].get("fields", {}).keys()))
        return

    fields = record.get("fields", {})
    print(f"📋 最新记录日期: {fields.get('预测覆盖日期')}")

    # 获取实际价格
    actual = fetch_actual_price()
    if not actual:
        print("❌ 无法获取实际价格")
        return

    print(f"📝 回填实际价格: {actual} 元/吨")
    result = update_actual_price(app_token, table_id, token, record["record_id"], actual)
    print(f"📥 回填结果: {result}")

    # 推送验证结果
    send_backfill_card(webhook, record)
    print("✅ 回填完成")


if __name__ == "__main__":
    main()
