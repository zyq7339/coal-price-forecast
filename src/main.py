import os
from data_fetcher import fetch_all_data
from predictor import call_deepseek, parse_prediction
from feishu_notifier import send_prediction_card


def main():
    webhook = os.environ.get("FEISHU_WEBHOOK")
    api_key = os.environ.get("DEEPSEEK_API_KEY")

    if not all([webhook, api_key]):
        print("❌ 缺少环境变量")
        print(f"   FEISHU_WEBHOOK: {'已设置' if webhook else '缺失'}")
        print(f"   DEEPSEEK_API_KEY: {'已设置' if api_key else '缺失'}")
        return

    print("📡 正在采集数据...")
    data = fetch_all_data()

    print(f"   CCTD: {data['cctd']} 元/吨")
    print(f"   CCI: {data['cci']} 元/吨")
    print(f"   海运费: {data['freight']} 元/吨")
    print(f"   运费周变化: {data['freight_change']}%")
    print(f"   北方库存: {data['inventory']} 万吨")
    print(f"   电厂库存: {data['power']['inventory']} 万吨")
    print(f"   电厂日耗: {data['power']['consumption']} 万吨")
    print(f"   长江口参考价: {data['yangtze']} 元/吨")
    print(f"   今日日期: {data['today']}")

    print("🧠 正在调用 AI 生成预测...")
    report = call_deepseek(data, api_key)
    prediction = parse_prediction(report)

    # 补充海运费数据
    prediction["freight"] = data["freight"]
    prediction["freight_change"] = data["freight_change"]

    print(f"   解析结果: 预测区间 {prediction.get('lower', '?')} - {prediction.get('upper', '?')} 元/吨")
    print(f"   市场阶段: {prediction.get('market_stage', '')}")
    print(f"   海运费: {prediction.get('freight')} 元/吨")
    print(f"   运费周变化: {prediction.get('freight_change', 'N/A')}%")

    print("📤 正在推送飞书卡片...")
    send_prediction_card(webhook, prediction)

    print("✅ 预测完成！")


if __name__ == "__main__":
    main()
