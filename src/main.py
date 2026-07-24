import os
from data_fetcher import fetch_all_data
from predictor import call_deepseek, parse_prediction
from feishu_notifier import send_prediction_card
from bitable_writer import write_prediction, get_tenant_access_token


def main():
    webhook = os.environ.get("FEISHU_WEBHOOK")
    api_key = os.environ.get("DEEPSEEK_API_KEY")
    app_token = os.environ.get("BITABLE_APP_TOKEN")
    table_id = os.environ.get("BITABLE_TABLE_ID")
    app_id = os.environ.get("FEISHU_APP_ID")
    app_secret = os.environ.get("FEISHU_APP_SECRET")

    if not all([webhook, api_key, app_token, table_id, app_id, app_secret]):
        print("❌ 缺少环境变量，请检查 GitHub Secrets 配置")
        return

    print("📡 正在采集数据...")
    data = fetch_all_data()

    print("🧠 正在调用 AI 生成预测...")
    report = call_deepseek(data, api_key)
    prediction = parse_prediction(report)

    print("📝 正在写入多维表格...")
    token = get_tenant_access_token(app_id, app_secret)
    write_prediction(app_token, table_id, token, prediction)

    print("📤 正在推送飞书卡片...")
    send_prediction_card(webhook, prediction)

    print("✅ 预测完成！")


if __name__ == "__main__":
    main()
