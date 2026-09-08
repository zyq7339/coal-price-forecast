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

    # 获取当前数据
    data = fetch_all_data()

    # 构造周预测Prompt
    prompt = f"""请基于以下最新数据，生成本周（{datetime.now().strftime('%Y年%m月%d日')}起）煤炭行情周预测报告。

【当前数据】
- 长江口5000K：{data['yangtze']}元/吨
- 北方港口CCTD 5000K：{data['cctd']}元/吨
- 北方三港库存：{data['inventory']}万吨
- 六大电厂库存：{data['power']['inventory']}万吨
- 六大电厂日耗：{data['power']['consumption']}万吨
- 海运费：{data['freight']}元/吨
- 运费周变化：{data['freight_change']}%

【输出格式】
本周走势预测：
- 预测区间：XXX-XXX元/吨（长江口5000K）
- 整体判断：上涨/震荡/下跌
- 核心驱动因素：1.XXX 2.XXX 3.XXX

操作建议：XXX
风险提示：XXX
"""

    report = call_deepseek_custom(prompt, api_key)
    send_text(webhook, f"📈 煤炭周预测\n\n{report}")
    print("✅ 周预测完成")


if __name__ == "__main__":
    main()
