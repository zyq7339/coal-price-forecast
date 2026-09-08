import os
from datetime import datetime, timedelta
from data_fetcher import fetch_all_data
from predictor import call_deepseek, parse_prediction
from feishu_notifier import send_prediction_card
from bitable_writer import (
    write_prediction,
    get_tenant_access_token,
    find_record_by_date
)


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

    # 补充当日海运费数据
    prediction["freight"] = data["freight"]

    # ---- 新增：计算真实的运费周变化 ----
    try:
        today_str = data['today']
        today_dt = datetime.strptime(today_str, "%Y-%m-%d")
        last_week_dt = today_dt - timedelta(days=7)
        last_week_str = last_week_dt.strftime("%Y-%m-%d")
        print(f"🔍 查找上周同期记录: {last_week_str}")

        # 获取 token 用于查询
        token = get_tenant_access_token(app_id, app_secret)
        last_record = find_record_by_date(app_token, table_id, token, last_week_str)
        if last_record:
            last_freight = last_record.get("fields", {}).get("海运费")
            if last_freight and last_freight != 0:
                current_freight = data['freight']
                change_pct = (current_freight - last_freight) / last_freight * 100
                change_pct = round(change_pct, 2)
                prediction["freight_change"] = change_pct
                print(f"📊 实际运费周变化: {change_pct}%")
            else:
                print("⚠️ 上周同期记录无海运费数据，保留 AI 默认值")
        else:
            print(f"⚠️ 未找到 {last_week_str} 的记录，保留 AI 默认值")
    except Exception as e:
        print(f"⚠️ 计算运费周变化时出错: {e}，保留 AI 默认值")

    # 若计算失败或没有历史数据，AI 默认值可能是 "0"，我们保留它
    # 但可以设置一个更合理的默认值，比如从数据中推断（此处维持原样）

    print(f"   解析结果: 预测区间 {prediction.get('lower', '?')} - {prediction.get('upper', '?')} 元/吨")
    print(f"   市场阶段: {prediction.get('market_stage', '')}")
    print(f"   海运费: {prediction.get('freight')} 元/吨")
    print(f"   运费周变化: {prediction.get('freight_change', 'N/A')}%")

    print("📝 正在写入多维表格...")
    # token 已在上面获取，可直接复用
    write_prediction(app_token, table_id, token, prediction)

    print("📤 正在推送飞书卡片...")
    send_prediction_card(webhook, prediction)

    print("✅ 预测完成！")


if __name__ == "__main__":
    main()
