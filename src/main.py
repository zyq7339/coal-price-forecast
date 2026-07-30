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
        print("❌ 缺少环境变量")
        return

    print("📡 正在采集数据...")
    data = fetch_all_data()

    print(f"   CCTD: {data['cctd']} 元/吨")
    print(f"   CCI: {data['cci']} 元/吨")
    print(f"   海运费: {data['freight']} 元/吨")
    print(f"   北方库存: {data['inventory']} 万吨")
    print(f"   电厂库存: {data['power']['inventory']} 万吨")
    print(f"   电厂日耗: {data['power']['consumption']} 万吨")
    print(f"   长江口参考价: {data['yangtze']} 元/吨")
    print(f"   今日日期: {data['today']}")

    print("🧠 正在调用 AI 生成预测...")
    report = call_deepseek(data, api_key)
    prediction = parse_prediction(report)

    # 补充海运费数据（用于写入表格和计算周变化）
    prediction["freight"] = data["freight"]

    print(f"   解析结果: 预测区间 {prediction.get('lower', '?')} - {prediction.get('upper', '?')} 元/吨")
    print(f"   市场阶段: {prediction.get('market_stage', '')}")
    print(f"   海运费: {prediction.get('freight')} 元/吨")

    print("📝 正在写入多维表格...")
    token = get_tenant_access_token(app_id, app_secret)
    write_prediction(app_token, table_id, token, prediction)

    print("📤 正在推送飞书卡片...")
    send_prediction_card(webhook, prediction)

    print("✅ 预测完成！")


if __name__ == "__main__":
    main()
