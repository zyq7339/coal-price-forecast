import requests
import re
from datetime import datetime
from bs4 import BeautifulSoup

# ============================================================
# 配置
# ============================================================
HEADERS = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}

# ============================================================
# CCTD价格采集（动态发现最新文章）
# ============================================================
def fetch_cctd_price():
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

# ============================================================
# CCI指数采集
# ============================================================
def fetch_cci_price():
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

# ============================================================
# 运费采集（从上海航运交易所）
# ============================================================
def fetch_freight():
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

# ============================================================
# 库存采集（从中国太原煤炭价格指数）
# ============================================================
def fetch_inventory():
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

# ============================================================
# 电厂数据采集
# ============================================================
def fetch_power_data():
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

# ============================================================
# 长江口价格采集
# ============================================================
def fetch_yangtze_price():
    try:
        url = "https://lexotech.com/news/news-content?did=6cf397d7eeb340677a37187c0fc25e7a"
        resp = requests.get(url, headers=HEADERS, timeout=10)
        soup = BeautifulSoup(resp.text, 'html.parser')
        text = soup.get_text()
        match = re.search(r'长江口参考价格.*?5000卡\s+(\d+)[－-](\d+)', text, re.DOTALL)
        if match:
            return (int(match.group(1)) + int(match.group(2))) // 2
        return None
    except Exception as e:
        print(f"⚠️ 长江口价格采集失败: {e}")
        return None

def fetch_actual_price():
    return fetch_yangtze_price()

# ============================================================
# 主采集函数
# ============================================================
def fetch_all_data():
    print("📡 正在从公开网页采集数据...")
    cctd = fetch_cctd_price()
    cci = fetch_cci_price()
    freight = fetch_freight()
    freight_change = fetch_freight_change()
    inventory = fetch_inventory()
    power = fetch_power_data()
    yangtze = fetch_yangtze_price()

    data = {
        "cctd": cctd if cctd else 871,
        "cci": cci if cci else 870,
        "freight": freight if freight else 48.0,
        "freight_change": freight_change,  # 新增预计算值
        "inventory": inventory if inventory else 2282,
        "power": power,
        "yangtze": yangtze if yangtze else 880,
        "today": datetime.now().strftime("%Y-%m-%d")
    }

    print(f"📊 采集完成:")
    print(f"   CCTD: {data['cctd']} 元/吨")
    print(f"   CCI: {data['cci']} 元/吨")
    print(f"   海运费: {data['freight']} 元/吨")
    print(f"   运费周变化: {data['freight_change']}%")
    print(f"   北方库存: {data['inventory']} 万吨")
    print(f"   电厂库存: {data['power']['inventory']} 万吨")
    print(f"   电厂日耗: {data['power']['consumption']} 万吨")
    print(f"   长江口参考价: {data['yangtze']} 元/吨")
    return data
