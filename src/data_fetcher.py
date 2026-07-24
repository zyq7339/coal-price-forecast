import requests
from datetime import datetime

# ============================================================
# TODO: 以下为临时模拟数据，请尽快替换为真实 API 调用
# ============================================================

def fetch_cctd_price():
    """获取 CCTD 5000K 价格"""
    # TODO: 替换为真实 API
    return 735  # 临时模拟值

def fetch_cci_price():
    """获取 CCI5000 指数"""
    return 734  # 临时模拟值

def fetch_freight():
    """获取海运费（秦皇岛→张家港 4-5万吨）"""
    return 41.7  # 临时模拟值

def fetch_inventory():
    """获取北方三港库存（万吨）"""
    return 2837  # 临时模拟值

def fetch_power_data():
    """获取六大电厂库存和日耗"""
    return {
        "inventory": 1455.5,   # 万吨
        "consumption": 87.5    # 万吨
    }

def fetch_actual_price():
    """获取昨日实际价格（用于回填）"""
    return 805  # 临时模拟值

def fetch_all_data():
    """采集所有数据，返回字典（包含当前日期）"""
    return {
        "cctd": fetch_cctd_price(),
        "cci": fetch_cci_price(),
        "freight": fetch_freight(),
        "inventory": fetch_inventory(),
        "power": fetch_power_data(),
        "today": datetime.now().strftime("%Y-%m-%d"),
    }
