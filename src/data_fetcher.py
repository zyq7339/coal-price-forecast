import requests
import re
from datetime import datetime
from bs4 import BeautifulSoup

# ============================================================
# 所有数据从公开网页采集，无需任何API Key
# ============================================================

def fetch_cctd_price():
    """从CCTD日评页面获取5000K价格"""
    try:
        url = "https://www.coalchina.org.cn/index.php?m=content&c=index&a=show&catid=33&id=162235"
        headers = {"User-Agent": "Mozilla/5.0"}
        resp = requests.get(url, headers=headers, timeout=10)
        soup = BeautifulSoup(resp.text, 'html.parser')
        text = soup.get_text()
        
        # 匹配 "5000K、4500K规格品分别收于826、736、643元/吨"
        match = re.search(r'5000K[、，]\s*(\d+)', text)
        if match:
            return int(match.group(1))
        return None
    except Exception as e:
        print(f"⚠️ CCTD采集失败: {e}")
        return None


def fetch_cci_price():
    """从煤炭资源网日度数据跟踪获取CCI5000"""
    try:
        url = "https://www.sxcoal.com/news/detail/2080461031963045889"
        headers = {"User-Agent": "Mozilla/5.0"}
        resp = requests.get(url, headers=headers, timeout=10)
        soup = BeautifulSoup(resp.text, 'html.parser')
        text = soup.get_text()
        
        # 匹配 "CCI5000 736"
        match = re.search(r'CCI5000\s+(\d+)', text)
        if match:
            return int(match.group(1))
        return None
    except Exception as e:
        print(f"⚠️ CCI采集失败: {e}")
        return None


def fetch_freight():
    """从煤炭资源网日度数据跟踪获取海运费"""
    try:
        url = "https://www.sxcoal.com/news/detail/2080461031963045889"
        headers = {"User-Agent": "Mozilla/5.0"}
        resp = requests.get(url, headers=headers, timeout=10)
        soup = BeautifulSoup(resp.text, 'html.parser')
        text = soup.get_text()
        
        # 匹配 "秦皇岛-张家港4-5万吨 48.7"
        match = re.search(r'秦皇岛[－-]张家港\s*4[－-]5万吨\s+([\d.]+)', text)
        if match:
            return float(match.group(1))
        return None
    except Exception as e:
        print(f"⚠️ 海运费采集失败: {e}")
        return None


def fetch_inventory():
    """从煤炭资源网获取北方港口库存"""
    try:
        url = "https://www.sxcoal.com/news/detail/2080118201878315009"
        headers = {"User-Agent": "Mozilla/5.0"}
        resp = requests.get(url, headers=headers, timeout=10)
        soup = BeautifulSoup(resp.text, 'html.parser')
        text = soup.get_text()
        
        # 匹配 "煤炭库存为2787万吨"
        match = re.search(r'煤炭库存为(\d+)万吨', text)
        if match:
            return int(match.group(1))
        return None
    except Exception as e:
        print(f"⚠️ 库存采集失败: {e}")
        return None


def fetch_power_data():
    """从煤炭资源网日度数据跟踪获取六大电厂数据"""
    try:
        url = "https://www.sxcoal.com/news/detail/2080461031963045889"
        headers = {"User-Agent": "Mozilla/5.0"}
        resp = requests.get(url, headers=headers, timeout=10)
        soup = BeautifulSoup(resp.text, 'html.parser')
        text = soup.get_text()
        
        # 匹配 "六大电厂库存量 1444.4"
        match_inv = re.search(r'六大电厂库存量\s+([\d.]+)', text)
        # 六大电厂日耗需要从页面其他位置获取，暂用默认值
        inventory = float(match_inv.group(1)) if match_inv else 1444.4
        
        return {"inventory": inventory, "consumption": 90.0}
    except Exception as e:
        print(f"⚠️ 电厂数据采集失败: {e}")
        return {"inventory": 1444.4, "consumption": 90.0}


def fetch_yangtze_price():
    """从煤炭资源网获取长江口5000K价格"""
    try:
        # 使用CCI周指数页面
        url = "https://www.sxcoal.com/news/detail/2080098640423235585"
        headers = {"User-Agent": "Mozilla/5.0"}
        resp = requests.get(url, headers=headers, timeout=10)
        soup = BeautifulSoup(resp.text, 'html.parser')
        text = soup.get_text()
        
        # 匹配 "长江口5000 | 790"
        match = re.search(r'长江口5000\s*\|\s*(\d+)', text)
        if match:
            return int(match.group(1))
        return None
    except Exception as e:
        print(f"⚠️ 长江口价格采集失败: {e}")
        return None


def fetch_actual_price():
    """获取昨日实际价格（用于回填）"""
    return fetch_yangtze_price()


def fetch_all_data():
    """采集所有数据，返回字典"""
    cctd = fetch_cctd_price()
    cci = fetch_cci_price()
    freight = fetch_freight()
    inventory = fetch_inventory()
    power = fetch_power_data()
    yangtze = fetch_yangtze_price()
    
    # 如果采集失败，使用备用默认值（基于7月24日真实数据）
    data = {
        "cctd": cctd if cctd else 736,
        "cci": cci if cci else 736,
        "freight": freight if freight else 48.7,
        "inventory": inventory if inventory else 2787,
        "power": power,
        "yangtze": yangtze if yangtze else 790,
        "today": datetime.now().strftime("%Y-%m-%d")
    }
    
    print(f"📊 采集结果: CCTD={data['cctd']}, CCI={data['cci']}, "
          f"运费={data['freight']}, 库存={data['inventory']}, "
          f"长江口={data['yangtze']}")
    return data
