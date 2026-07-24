import requests
from datetime import datetime

# ============================================================
# TODO: 以下为临时模拟数据，请尽快替换为真实 API 调用
# ============================================================

def fetch_cctd_price():
    """获取 CCTD 5000K 价格"""
    # TODO: 替换为真实 API
    # 当前（2026年7月）CCTD 5000K 约 730-740元/吨（北方港口）
    return 735  # 更新为当前合理值


def fetch_cci_price():
    """获取 CCI5000 指数"""
    # 当前（2026年7月）CCI5000 约 732-736元/吨
    return 734


def fetch_freight():
    """获取海运费（秦皇岛→张家港 4-5万吨）"""
    # 当前（2026年7月）海运费约 40-42元/吨
    return 41.7


def fetch_inventory():
    """获取北方三港库存（万吨）"""
    # 当前（2026年7月）北方三港库存约 2800-2900万吨
    return 2837


def fetch_power_data():
    """获取六大电厂库存和日耗"""
    return {
        "inventory": 1455.5,   # 万吨
        "consumption": 87.5    # 万吨
    }


def fetch_actual_price():
    """获取昨日实际价格（用于回填）"""
    # 当前（2026年7月）长江口5000K实际价格约 800-810元/吨
    return 805  # 临时模拟值


def fetch_all_data():
    """采集所有数据，返回字典（包含当前日期）"""
    return {
        "cctd": fetch_cctd_price(),
        "cci": fetch_cci_price(),
        "freight": fetch_freight(),
        "inventory": fetch_inventory(),
        "power": fetch_power_data(),
        "today": datetime.now().strftime("%Y-%m-%d"),      # 新增：今日日期
        "yesterday": datetime.now().strftime("%Y-%m-%d")   # 新增：昨日日期
    }
