import os
from data_fetcher import fetch_all_data
from predictor import call_deepseek, parse_prediction
from feishu_notifier import send_prediction_card
from bitable_writer import write_prediction, get_tenant_access_token


def main():
    # 读取环境变量
    webhook = os.environ.get("FEISHU_WEBHOOK")
    api_key = os.environ.get("DEEPSEEK_API_KEY")
    app_token = os.environ.get("BITABLE_APP_TOKEN")
    table_id = os.environ.get("BITABLE_TABLE_ID")
    app_id = os.environ.get("FEISHU_APP_ID")
    app_secret = os.environ.get("FEISHU_APP_SECRET")

    # 检查是否所有变量都已配置
    if not all([webhook, api_key, app_token, table_id, app_id, app_secret]):
        print("❌ 缺少环境变量，请检查 GitHub Secrets 配置")
        print("   FEISHU_WEBHOOK:", "已设置" if webhook else "缺失")
        print("   DEEPSEEK_API_KEY:", "已设置" if api_key else "缺失")
        print("   BITABLE_APP_TOKEN:", "已设置" if app_token else "缺失")
        print("   BITABLE_TABLE_ID:", "已设置" if table_id else "缺失")
        print("   FEISHU_APP_ID:", "已设置" if app_id else "缺失")
        print("   FEISHU_APP_SECRET:", "已设置" if app_secret else "缺失")
        return

    print("📡 正在采集数据...")
    data = fetch_all_data()

    # 打印采集到的数据，便于排查
    print(f"   CCTD: {data['cctd']} 元/吨")
    print(f"   CCI: {data['cci']} 元/吨")
    print(f"   海运费: {data['freight']} 元/吨")
    print(f"   北方库存: {data['inventory']} 万吨")
    print(f"   电厂库存: {data['power']['inventory']} 万吨")
    print(f"   电厂日耗: {data['power']['consumption']} 万吨")
    print(f"   今日日期: {data['today']}")

    print("🧠 正在调用 AI 生成预测...")
    report = call_deepseek(data, api_key)

    # 可选：打印原始报告以便调试
    # print("原始报告:\n", report)

    prediction = parse_prediction(report)
    print(f"   解析结果: 预测区间 {prediction.get('lower', '?')} - {prediction.get('upper', '?')} 元/吨")
    print(f"   市场阶段: {prediction.get('market_stage', '')}")

    print("📝 正在写入多维表格...")
    token = get_tenant_access_token(app_id, app_secret)
    write_prediction(app_token, table_id, token, prediction)

    print("📤 正在推送飞书卡片...")
    send_prediction_card(webhook, prediction)

    print("✅ 预测完成！")


if __name__ == "__main__":
    main()
