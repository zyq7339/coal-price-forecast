import requests
from datetime import datetime

# ============================================================
# TODO: 以下函数中的模拟数据，请替换为真实 API 调用
# ============================================================

def fetch_cctd_price():
    """获取 CCTD 5000K 价格"""
    # 示例：真实 API 调用
    # url = "https://api.cctd.com.cn/price/5000K"
    # headers = {"Authorization": "Bearer YOUR_TOKEN"}
    # resp = requests.get(url, headers=headers)
    # return resp.json()["price"]
    return 732  # 临时模拟值


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
    # 实际应从数据源获取
    return 805  # 临时模拟值


def fetch_all_data():
    """采集所有数据，返回字典"""
    return {
        "cctd": fetch_cctd_price(),
        "cci": fetch_cci_price(),
        "freight": fetch_freight(),
        "inventory": fetch_inventory(),
        "power": fetch_power_data(),
        "date": datetime.now().strftime("%Y-%m-%d")
    }
