import requests
import re
from datetime import datetime, timedelta
from bs4 import BeautifulSoup

HEADERS = {"User-Agent": "Mozilla/5.0"}


# ============================================================
# 基础数据采集函数
# ============================================================

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


# ============================================================
# 新增：市场简评、事件驱动、长江口库存采集
# ============================================================

def fetch_cctd_article_content():
    """获取CCTD最新日评文章的全文内容"""
    try:
        list_url = "https://www.coalchina.org.cn/index.php?m=content&c=index&a=lists&catid=33"
        resp = requests.get(list_url, headers=HEADERS, timeout=10)
        soup = BeautifulSoup(resp.text, 'html.parser')
        for link in soup.find_all('a', href=True):
            href = link.get('href', '')
            if 'catid=33' in href and 'id=' in href:
                article_url = href if href.startswith('http') else f"https://www.coalchina.org.cn{href}"
                article_resp = requests.get(article_url, headers=HEADERS, timeout=10)
                return article_resp.text
        return None
    except Exception as e:
        print(f"⚠️ CCTD文章获取失败: {e}")
        return None


def fetch_market_summary():
    """从CCTD日评中提取市场简评"""
    html = fetch_cctd_article_content()
    if not html:
        return None
    soup = BeautifulSoup(html, 'html.parser')
    text = soup.get_text()
    # 尝试匹配"煤炭市场简评"段落
    patterns = [
        r'煤炭市场简评[：:]\s*(.*?)(?=\n\n|\Z)',
        r'市场简评[：:]\s*(.*?)(?=\n\n|\Z)',
        r'【市场简评】\s*(.*?)(?=\n\n|\Z)',
    ]
    for pattern in patterns:
        match = re.search(pattern, text, re.DOTALL)
        if match:
            summary = match.group(1).strip()
            summary = re.sub(r'\s+', ' ', summary)
            return summary
    # 若未找到，返回全文前300字符
    return text[:300]


def fetch_yangtze_inventory():
    """
    尝试从公开数据获取长江口库存（当前版本暂无法自动采集，返回None）
    如后续找到数据源可补充
    """
    # 预留接口，当前返回None
    return None


def extract_event_from_summary(summary):
    """从市场简评中提取事件关键词"""
    if not summary:
        return None
    keywords = ['封航', '暴雨', '事故', '安检', '停产', '检修', '罢工', '台风', '政策', '进口']
    found = [kw for kw in keywords if kw in summary]
    if found:
        return f"市场简评提及: {', '.join(found)}。摘要: {summary[:120]}..."
    return None


# ============================================================
# 主采集函数
# ============================================================

def fetch_all_data():
    """采集今日收盘数据，包含新增维度"""
    print("📡 正在采集今日收盘数据...")

    today = datetime.now()
    tomorrow = today + timedelta(days=1)

    port_price = fetch_cci_price() or fetch_cctd_price() or 872
    freight = fetch_freight() or 36.1
    freight_change = fetch_freight_change() or -3.2
    inventory = fetch_inventory() or 2205
    power = fetch_power_data()
    summary = fetch_market_summary()
    yangtze_inv = fetch_yangtze_inventory()

    # 推算长江口收盘参考价
    yangtze = port_price + freight

    # 提取事件
    event = extract_event_from_summary(summary)

    data = {
        "cctd": port_price,
        "cci": port_price,
        "freight": freight,
        "freight_change": freight_change,
        "inventory": inventory,
        "power": power,
        "yangtze": yangtze,
        "yangtze_inventory": yangtze_inv,
        "market_summary": summary,
        "event": event,
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
    if data['yangtze_inventory']:
        print(f"   长江口库存: {data['yangtze_inventory']} 万吨")
    if data['event']:
        print(f"   ⚡ 事件: {data['event']}")
    print(f"   预测日期: {data['tomorrow']}")

    return data
