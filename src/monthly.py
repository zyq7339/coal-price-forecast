import os
from datetime import datetime
from data_fetcher import fetch_all_data
from predictor import call_deepseek_custom
from feishu_notifier import send_text


def main():
    webhook = os.environ.get("FEISHU_WEBHOOK")
    api_key = os.environ.get("DEEPSEEK_API_KEY")

    if not all([webhook, api_key]):
        print("❌ 缺少环境变量")
        return

    data = fetch_all_data()

    prompt = f"""请基于以下最新数据，生成本月（{datetime.now().strftime('%Y年%m月')}）煤炭行情月度预测报告。

【当前数据】
- 长江口5000K：{data['yangtze']}元/吨
- 北方港口CCTD 5000K：{data['cctd']}元/吨
- 北方三港库存：{data['inventory']}万吨
- 六大电厂库存：{data['power']['inventory']}万吨
- 六大电厂日耗：{data['power']['consumption']}万吨
- 海运费：{data['freight']}元/吨

【输出格式】
本月价格中枢预测：
- 预测均价区间：XXX-XXX元/吨
- 趋势判断：上涨/震荡/下跌

本月核心驱动逻辑：
1. XXX
2. XXX
3. XXX

本月采购策略建议：XXX
风险提示：XXX
"""

    report = call_deepseek_custom(prompt, api_key)
    send_text(webhook, f"📅 煤炭月预测\n\n{report}")
    print("✅ 月预测完成")


if __name__ == "__main__":
    main()
