import requests
from datetime import datetime

# ============================================================
# TODO: 以下为临时模拟数据，请尽快替换为真实 API 调用
# ============================================================

def fetch_cctd_price():
    """获取 CCTD 5000K 价格（北方港口）"""
    # TODO: 替换为真实 API
    return 732


def fetch_cci_price():
    """获取 CCI5000 指数（北方港口）"""
    return 734


def fetch_freight():
    """获取海运费（秦皇岛→张家港 4-5万吨）"""
    return 41.7


def fetch_inventory():
    """获取北方三港库存（万吨）"""
    return 2837


def fetch_power_data():
    """获取六大电厂库存和日耗"""
    return {
        "inventory": 1455.5,
        "consumption": 87.5
    }


def fetch_yangtze_price():
    """获取长江口5000K实际价格（预测基准）"""
    # TODO: 替换为真实 API
    return 805


def fetch_actual_price():
    """获取昨日实际价格（用于回填）"""
    return 805


def fetch_all_data():
    """采集所有数据，返回字典"""
    return {
        "cctd": fetch_cctd_price(),
        "cci": fetch_cci_price(),
        "freight": fetch_freight(),
        "inventory": fetch_inventory(),
        "power": fetch_power_data(),
        "yangtze": fetch_yangtze_price(),
        "today": datetime.now().strftime("%Y-%m-%d")
    }
