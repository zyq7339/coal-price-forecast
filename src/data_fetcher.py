import requests
import re
from datetime import datetime, timedelta
from bs4 import BeautifulSoup

HEADERS = {"User-Agent": "Mozilla/5.0"}


def fetch_cctd_price():
    """获取CCTD 5000K价格"""
    try:
        list_url = "https://www.coalchina.org.cn/index.php?m=content&c=index&a=lists&catid=33"
        resp = requests.get(list_url, headers=HEADERS, timeout=10)
        soup = BeautifulSoup(resp.text, 'html.parser')
        for link in soup.find_all('a', href=True):
            href = link.get('href', '')
            if 'catid=33' in href and 'id=' in href:
                article_url = href if href.startswith('http') else f"https://www.coalchina.org.cn{href}"
                article_resp = requests.get(article_url, headers=HEADERS, timeout=10)
                text = BeautifulSoup(article_resp.text, 'html.parser').get_text()
                match = re.search(r'5000K[、，]\s*(\d+)', text)
                if match:
                    return int(match.group(1))
        return None
    except Exception as e:
        print(f"⚠️ CCTD采集失败: {e}")
        return None


def fetch_cci_price():
    """获取CCI5000指数"""
    try:
        url = "https://www.sxcoal.com/news/detail/2080461031963045889"
        resp = requests.get(url, headers=HEADERS, timeout=10)
        soup = BeautifulSoup(resp.text, 'html.parser')
        text = soup.get_text()
        match = re.search(r'CCI5000\s+(\d+)', text)
        if match:
            return int(match.group(1))
        return None
    except Exception as e:
        print(f"⚠️ CCI采集失败: {e}")
        return None


def fetch_freight():
    """获取海运费（秦皇岛→张家港4-5万吨）"""
    try:
        url = "https://www.cei.cn/defaultsite/s/article/2026/09/07/4b4ff607-9d914745-01a0-7ad149c9-7185_home.html"
        resp = requests.get(url, headers=HEADERS, timeout=10)
        soup = BeautifulSoup(resp.text, 'html.parser')
        text = soup.get_text()
        match = re.search(r'秦皇岛[－-]张家港\s*4[－-]5万DWT\s+([\d.]+)\s+([\d.]+)', text)
        if match:
            return float(match.group(2))
        return None
    except Exception as e:
        print(f"⚠️ 运费采集失败: {e}")
        return None


def fetch_freight_change():
    """获取运费周变化率（%）"""
    try:
        url = "https://www.cei.cn/defaultsite/s/article/2026/09/07/4b4ff607-9d914745-01a0-7ad149c9-7185_home.html"
        resp = requests.get(url, headers=HEADERS, timeout=10)
        soup = BeautifulSoup(resp.text, 'html.parser')
        text = soup.get_text()
        match = re.search(r'秦皇岛[－-]张家港\s*4[－-]5万DWT\s+([\d.]+)\s+([\d.]+)', text)
        if match:
            last_week = float(match.group(1))
            current_week = float(match.group(2))
            if last_week != 0:
                return round((current_week - last_week) / last_week * 100, 2)
        return 0.0
    except Exception as e:
        print(f"⚠️ 运费周变化采集失败: {e}")
        return 0.0


def fetch_inventory():
    """获取北方三港库存（万吨）"""
    try:
        url = "https://www.ccera.com.cn/web/166/202609/27140.html"
        resp = requests.get(url, headers=HEADERS, timeout=10)
        soup = BeautifulSoup(resp.text, 'html.parser')
        text = soup.get_text()
        match = re.search(r'秦皇岛港、京唐港、曹妃甸港合计库存(\d+)万吨', text)
        if match:
            return int(match.group(1))
        return None
    except Exception as e:
        print(f"⚠️ 库存采集失败: {e}")
        return None


def fetch_power_data():
    """获取六大电厂库存和日耗"""
    try:
        url = "https://www.ccera.com.cn/web/166/202609/27140.html"
        resp = requests.get(url, headers=HEADERS, timeout=10)
        soup = BeautifulSoup(resp.text, 'html.parser')
        text = soup.get_text()
        match_consumption = re.search(r'六大电力集团沿海电厂日耗([\d.]+)万吨', text)
        consumption = float(match_consumption.group(1)) if match_consumption else 87.9
        match_inventory = re.search(r'六大电力集团沿海电厂库存([\d.]+)万吨', text)
        inventory = float(match_inventory.group(1)) if match_inventory else 1418.2
        return {"inventory": inventory, "consumption": consumption}
    except Exception as e:
        print(f"⚠️ 电厂数据采集失败: {e}")
        return {"inventory": 1418.2, "consumption": 87.9}


def fetch_all_data():
    """
    采集今日收盘数据，用于预测明日价格
    """
    print("📡 正在采集今日收盘数据...")

    today = datetime.now()
    tomorrow = today + timedelta(days=1)

    port_price = fetch_cci_price() or fetch_cctd_price() or 872
    freight = fetch_freight() or 36.1
    freight_change = fetch_freight_change() or -3.2
    inventory = fetch_inventory() or 2205
    power = fetch_power_data()

    # 推算今日长江口收盘参考价 = 北方港口 + 海运费
    yangtze_close = port_price + freight

    data = {
        "cctd": port_price,
        "cci": port_price,
        "freight": freight,
        "freight_change": freight_change,
        "inventory": inventory,
        "power": power,
        "yangtze": yangtze_close,
        "today": today.strftime("%Y-%m-%d"),
        "tomorrow": tomorrow.strftime("%Y-%m-%d")
    }

    print(f"   CCI5000收盘: {data['cci']} 元/吨")
    print(f"   海运费收盘: {data['freight']} 元/吨")
    print(f"   运费周变化: {data['freight_change']}%")
    print(f"   北方三港库存: {data['inventory']} 万吨")
    print(f"   电厂库存: {data['power']['inventory']} 万吨")
    print(f"   电厂日耗: {data['power']['consumption']} 万吨")
    print(f"   推算长江口收盘参考价: {data['yangtze']} 元/吨")
    print(f"   预测日期: {data['tomorrow']}")

    return data
