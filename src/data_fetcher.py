import requests
import re
import urllib3
from datetime import datetime, timedelta
from bs4 import BeautifulSoup

# 禁用 SSL 警告
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

HEADERS = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}


# ============================================================
# 动态发现最新文章工具
# ============================================================

def get_latest_cctd_article_url():
    """从CCTD列表页获取最新日评文章URL"""
    try:
        list_url = "https://www.coalchina.org.cn/index.php?m=content&c=index&a=lists&catid=33"
        resp = requests.get(list_url, headers=HEADERS, timeout=15, verify=False)
        soup = BeautifulSoup(resp.text, 'html.parser')
        for link in soup.find_all('a', href=True):
            href = link.get('href', '')
            if 'catid=33' in href and 'id=' in href:
                full_url = href if href.startswith('http') else f"https://www.coalchina.org.cn{href}"
                return full_url
        return None
    except Exception as e:
        print(f"⚠️ 获取CCTD列表失败: {e}")
        return None


def get_latest_sxcoal_article_url(keyword="日度数据跟踪"):
    """通过站内搜索获取煤炭资源网最新相关文章URL"""
    try:
        search_url = f"https://www.sxcoal.com/search?keyword={keyword}"
        resp = requests.get(search_url, headers=HEADERS, timeout=15, verify=False)
        soup = BeautifulSoup(resp.text, 'html.parser')
        for link in soup.find_all('a', href=True):
            href = link.get('href', '')
            if '/news/detail/' in href:
                full_url = href if href.startswith('http') else f"https://www.sxcoal.com{href}"
                return full_url
        return None
    except Exception as e:
        print(f"⚠️ 搜索煤炭资源网失败: {e}")
        return None


# ============================================================
# 价格采集
# ============================================================

def fetch_port_price_from_cctd():
    """从CCTD最新日评中提取北方港口5000K参考报价"""
    article_url = get_latest_cctd_article_url()
    if not article_url:
        return None
    try:
        resp = requests.get(article_url, headers=HEADERS, timeout=15, verify=False)
        soup = BeautifulSoup(resp.text, 'html.parser')
        text = soup.get_text()
        # 匹配类似"5000K、4500K规格品分别收于959、871、790元/吨"
        match = re.search(r'5000K[、，]\s*(\d+)', text)
        if match:
            return int(match.group(1))
        # 匹配报价区间
        match_range = re.search(r'5000K[：:]\s*(\d+)\s*[-~]\s*(\d+)', text)
        if match_range:
            return (int(match_range.group(1)) + int(match_range.group(2))) // 2
        return None
    except Exception as e:
        print(f"⚠️ 从CCTD提取北方港报价失败: {e}")
        return None


def fetch_cci_price():
    """获取CCI5000指数"""
    article_url = get_latest_sxcoal_article_url("日度数据跟踪")
    if not article_url:
        return None
    try:
        resp = requests.get(article_url, headers=HEADERS, timeout=15, verify=False)
        soup = BeautifulSoup(resp.text, 'html.parser')
        text = soup.get_text()
        match = re.search(r'CCI5000\s+(\d+)', text)
        if match:
            return int(match.group(1))
        return None
    except Exception as e:
        print(f"⚠️ CCI采集失败: {e}")
        return None


def fetch_cctd_price():
    """获取CCTD 5000K价格（备用）"""
    article_url = get_latest_cctd_article_url()
    if not article_url:
        return None
    try:
        resp = requests.get(article_url, headers=HEADERS, timeout=15, verify=False)
        soup = BeautifulSoup(resp.text, 'html.parser')
        text = soup.get_text()
        match = re.search(r'5000K[、，]\s*(\d+)', text)
        if match:
            return int(match.group(1))
        return None
    except Exception as e:
        print(f"⚠️ CCTD采集失败: {e}")
        return None


# ============================================================
# 运费采集（多URL备用 + 超时重试）
# ============================================================

def fetch_freight():
    """获取海运费（秦皇岛→张家港4-5万吨）"""
    urls = [
        "https://www.cei.cn/defaultsite/s/article/2026/09/07/4b4ff607-9d914745-01a0-7ad149c9-7185_home.html",
        "https://www.sse.net.cn/index/cbcfi",  # 上海航运交易所备用
    ]
    for url in urls:
        try:
            resp = requests.get(url, headers=HEADERS, timeout=20, verify=False)
            soup = BeautifulSoup(resp.text, 'html.parser')
            text = soup.get_text()
            match = re.search(r'秦皇岛[－-]张家港\s*4[－-]5万DWT\s+([\d.]+)\s+([\d.]+)', text)
            if match:
                return float(match.group(2))
        except Exception as e:
            print(f"⚠️ 运费采集失败（{url[:30]}）: {e}")
            continue
    return None


def fetch_freight_change():
    """获取运费周变化率（%）"""
    urls = [
        "https://www.cei.cn/defaultsite/s/article/2026/09/07/4b4ff607-9d914745-01a0-7ad149c9-7185_home.html",
    ]
    for url in urls:
        try:
            resp = requests.get(url, headers=HEADERS, timeout=20, verify=False)
            soup = BeautifulSoup(resp.text, 'html.parser')
            text = soup.get_text()
            match = re.search(r'秦皇岛[－-]张家港\s*4[－-]5万DWT\s+([\d.]+)\s+([\d.]+)', text)
            if match:
                last_week = float(match.group(1))
                current_week = float(match.group(2))
                if last_week != 0:
                    return round((current_week - last_week) / last_week * 100, 2)
        except Exception as e:
            print(f"⚠️ 运费周变化采集失败: {e}")
            continue
    return 0.0


# ============================================================
# 库存、电厂、市场简评
# ============================================================

def fetch_inventory():
    """获取北方三港库存（万吨）"""
    try:
        url = "https://www.ccera.com.cn/web/166/202609/27140.html"
        resp = requests.get(url, headers=HEADERS, timeout=15, verify=False)
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
        resp = requests.get(url, headers=HEADERS, timeout=15, verify=False)
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


def fetch_market_summary():
    """从CCTD日评中提取市场简评"""
    article_url = get_latest_cctd_article_url()
    if not article_url:
        return None
    try:
        resp = requests.get(article_url, headers=HEADERS, timeout=15, verify=False)
        soup = BeautifulSoup(resp.text, 'html.parser')
        text = soup.get_text()
        patterns = [
            r'煤炭市场简评[：:]\s*(.*?)(?=\n\n|\Z)',
            r'市场简评[：:]\s*(.*?)(?=\n\n|\Z)',
        ]
        for pattern in patterns:
            match = re.search(pattern, text, re.DOTALL)
            if match:
                summary = re.sub(r'\s+', ' ', match.group(1).strip())
                return summary
        return text[:300]
    except Exception as e:
        print(f"⚠️ 市场简评获取失败: {e}")
        return None


def extract_event_from_summary(summary):
    """从市场简评中提取事件关键词"""
    if not summary:
        return None
    keywords = ['封航', '暴雨', '事故', '安检', '停产', '检修', '台风', '政策', '进口']
    found = [kw for kw in keywords if kw in summary]
    if found:
        return f"市场简评提及: {', '.join(found)}"
    return None


# ============================================================
# 主采集函数（含兜底与校验）
# ============================================================

def fetch_all_data():
    """采集今日收盘数据，长江口价格 = 北方港基准 + 运费"""
    print("📡 正在采集今日收盘数据...")

    today = datetime.now()
    tomorrow = today + timedelta(days=1)

    # 1. 北方港基准价
    port_price = None
    cctd_actual = fetch_port_price_from_cctd()
    if cctd_actual and 800 <= cctd_actual <= 1000:
        port_price = cctd_actual
        print(f"   ✅ 使用CCTD实际报价: {port_price} 元/吨")
    else:
        cci = fetch_cci_price()
        if cci and 800 <= cci <= 1000:
            # 根据库存动态溢价
            inv = fetch_inventory() or 2205
            if inv < 2300:
                premium = 25
            elif inv < 2500:
                premium = 20
            else:
                premium = 15
            port_price = cci + premium
            print(f"   ⚠️ 使用CCI+溢价: CCI={cci}, 溢价={premium}, 基准={port_price} 元/吨")
        else:
            # 兜底：使用近期市场实际值（2026年9月北方港5000K约900-915）
            port_price = 900
            print(f"   ⚠️ 所有价格源失败，使用兜底值: {port_price} 元/吨")

    # 2. 其他数据
    freight = fetch_freight()
    if not freight or not (20 <= freight <= 80):
        freight = 36.1
        print(f"   ⚠️ 运费采集失败，使用兜底值: {freight} 元/吨")
    else:
        print(f"   ✅ 海运费: {freight} 元/吨")

    freight_change = fetch_freight_change()
    inventory = fetch_inventory() or 2205
    power = fetch_power_data()
    summary = fetch_market_summary()
    event = extract_event_from_summary(summary)

    # 3. 推算长江口收盘参考价
    yangtze = port_price + freight

    data = {
        "cctd": port_price,
        "cci": port_price,
        "freight": freight,
        "freight_change": freight_change,
        "inventory": inventory,
        "power": power,
        "yangtze": yangtze,
        "market_summary": summary,
        "event": event,
        "today": today.strftime("%Y-%m-%d"),
        "tomorrow": tomorrow.strftime("%Y-%m-%d")
    }

    print(f"   北方港基准价: {data['cctd']} 元/吨")
    print(f"   海运费: {data['freight']} 元/吨")
    print(f"   运费周变化: {data['freight_change']}%")
    print(f"   北方三港库存: {data['inventory']} 万吨")
    print(f"   电厂库存: {data['power']['inventory']} 万吨")
    print(f"   电厂日耗: {data['power']['consumption']} 万吨")
    print(f"   推算长江口收盘参考价: {data['yangtze']} 元/吨")
    if data['event']:
        print(f"   ⚡ 事件: {data['event']}")
    print(f"   预测日期: {data['tomorrow']}")

    return data
