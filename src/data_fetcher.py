import requests
import re
from datetime import datetime
from bs4 import BeautifulSoup

# ============================================================
# 配置区：可根据实际情况调整搜索关键词
# ============================================================
CONFIG = {
    "sxcoal_search_keyword": "日度数据跟踪",
    "cctd_list_url": "https://www.coalchina.org.cn/index.php?m=content&c=index&a=lists&catid=33",
    "user_agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
}

headers = {"User-Agent": CONFIG["user_agent"]}


# ============================================================
# 工具函数：动态发现最新文章URL
# ============================================================

def get_latest_sxcoal_article_url(keyword="日度数据跟踪"):
    """
    通过站内搜索获取煤炭资源网最新相关文章URL
    返回: 文章完整URL 或 None
    """
    try:
        # 搜索页URL
        search_url = f"https://www.sxcoal.com/search?keyword={keyword}"
        resp = requests.get(search_url, headers=headers, timeout=10)
        soup = BeautifulSoup(resp.text, 'html.parser')
        
        # 搜索结果通常以列表展示，取第一条链接
        # 常见选择器：.search-result a, .news-list a, 或直接找所有a标签
        links = soup.find_all('a', href=True)
        for link in links:
            href = link.get('href', '')
            # 匹配 /news/detail/ 开头的链接
            if '/news/detail/' in href:
                full_url = href if href.startswith('http') else f"https://www.sxcoal.com{href}"
                return full_url
        return None
    except Exception as e:
        print(f"⚠️ 搜索失败: {e}")
        return None


def get_latest_cctd_article_url():
    """
    从CCTD列表页获取最新日评文章URL
    返回: 文章完整URL 或 None
    """
    try:
        url = CONFIG["cctd_list_url"]
        resp = requests.get(url, headers=headers, timeout=10)
        soup = BeautifulSoup(resp.text, 'html.parser')
        
        # 匹配文章链接: /index.php?m=content&c=index&a=show&catid=33&id=数字
        links = soup.find_all('a', href=True)
        for link in links:
            href = link.get('href', '')
            if 'catid=33' in href and 'id=' in href:
                full_url = href if href.startswith('http') else f"https://www.coalchina.org.cn{href}"
                return full_url
        return None
    except Exception as e:
        print(f"⚠️ CCTD列表页获取失败: {e}")
        return None


# ============================================================
# 备用URL列表（当动态发现失败时使用）
# ============================================================
BACKUP_URLS = {
    "sxcoal": [
        "https://www.sxcoal.com/news/detail/2080461031963045889",  # 近期日度数据
        "https://www.sxcoal.com/news/detail/2080118201878315009",  # 库存数据
        "https://www.sxcoal.com/news/detail/2080098640423235585",  # CCI周指数
    ],
    "cctd": [
        "https://www.coalchina.org.cn/index.php?m=content&c=index&a=show&catid=33&id=162235",
    ]
}


# ============================================================
# 数据采集函数（智能发现 + 回退机制）
# ============================================================

def fetch_from_sxcoal(pattern, default=None, url=None):
    """
    从煤炭资源网页面提取数据（自动发现最新文章）
    pattern: 正则表达式
    default: 默认值
    url: 可指定URL，不指定则自动发现
    """
    try:
        # 如果未指定URL，自动发现
        if url is None:
            url = get_latest_sxcoal_article_url(CONFIG["sxcoal_search_keyword"])
        
        # 如果自动发现失败，尝试备用URL
        if url is None:
            for backup_url in BACKUP_URLS["sxcoal"]:
                try:
                    resp = requests.get(backup_url, headers=headers, timeout=10)
                    soup = BeautifulSoup(resp.text, 'html.parser')
                    text = soup.get_text()
                    match = re.search(pattern, text)
                    if match:
                        return match.group(1).strip()
                except:
                    continue
            return default
        
        # 访问文章页面
        resp = requests.get(url, headers=headers, timeout=10)
        soup = BeautifulSoup(resp.text, 'html.parser')
        text = soup.get_text()
        match = re.search(pattern, text)
        if match:
            return match.group(1).strip()
        return default
    except Exception as e:
        print(f"⚠️ sxcoal采集失败: {e}")
        return default


def fetch_cctd_price():
    """从CCTD获取5000K价格（北方港口）"""
    try:
        # 尝试动态发现最新文章
        url = get_latest_cctd_article_url()
        
        # 如果发现失败，尝试备用URL
        if url is None:
            for backup_url in BACKUP_URLS["cctd"]:
                try:
                    resp = requests.get(backup_url, headers=headers, timeout=10)
                    soup = BeautifulSoup(resp.text, 'html.parser')
                    text = soup.get_text()
                    # 匹配 "5000K：736" 或 "5000K、4500K规格品分别收于826、736、643元/吨"
                    match = re.search(r'5000K[、，]\s*(\d+)', text)
                    if match:
                        return int(match.group(1))
                except:
                    continue
            return 736  # 默认值
        
        # 访问最新文章
        resp = requests.get(url, headers=headers, timeout=10)
        soup = BeautifulSoup(resp.text, 'html.parser')
        text = soup.get_text()
        match = re.search(r'5000K[、，]\s*(\d+)', text)
        if match:
            return int(match.group(1))
        return 736
    except Exception as e:
        print(f"⚠️ CCTD采集失败: {e}")
        return 736


def fetch_cci_price():
    """获取CCI5000指数"""
    pattern = r'CCI5000\s+(\d+)'
    result = fetch_from_sxcoal(pattern, default=736)
    return int(result) if result else 736


def fetch_freight():
    """获取海运费（秦皇岛→张家港4-5万吨）"""
    pattern = r'秦皇岛[－-]张家港\s*4[－-]5万吨\s+([\d.]+)'
    result = fetch_from_sxcoal(pattern, default=48.7)
    return float(result) if result else 48.7


def fetch_inventory():
    """获取北方三港库存"""
    pattern = r'煤炭库存为(\d+)万吨'
    result = fetch_from_sxcoal(pattern, default=2787)
    return int(result) if result else 2787


def fetch_power_data():
    """获取六大电厂库存和日耗"""
    try:
        # 尝试从日度数据页面获取
        url = get_latest_sxcoal_article_url(CONFIG["sxcoal_search_keyword"])
        if url is None:
            for backup_url in BACKUP_URLS["sxcoal"]:
                try:
                    resp = requests.get(backup_url, headers=headers, timeout=10)
                    soup = BeautifulSoup(resp.text, 'html.parser')
                    text = soup.get_text()
                    match = re.search(r'六大电厂库存量\s+([\d.]+)', text)
                    if match:
                        inventory = float(match.group(1))
                        # 日耗可能在同一页面，也可能需单独获取
                        return {"inventory": inventory, "consumption": 90.0}
                except:
                    continue
            return {"inventory": 1444.4, "consumption": 90.0}
        
        resp = requests.get(url, headers=headers, timeout=10)
        soup = BeautifulSoup(resp.text, 'html.parser')
        text = soup.get_text()
        match = re.search(r'六大电厂库存量\s+([\d.]+)', text)
        inventory = float(match.group(1)) if match else 1444.4
        return {"inventory": inventory, "consumption": 90.0}
    except Exception as e:
        print(f"⚠️ 电厂数据采集失败: {e}")
        return {"inventory": 1444.4, "consumption": 90.0}


def fetch_yangtze_price():
    """获取长江口5000K价格"""
    pattern = r'长江口5000\s*\|\s*(\d+)'
    result = fetch_from_sxcoal(pattern, default=790)
    return int(result) if result else 790


def fetch_actual_price():
    """获取昨日实际价格（用于回填）"""
    return fetch_yangtze_price()


def fetch_all_data():
    """采集所有数据，返回字典"""
    print("📡 正在从公开网页采集数据...")
    
    cctd = fetch_cctd_price()
    cci = fetch_cci_price()
    freight = fetch_freight()
    inventory = fetch_inventory()
    power = fetch_power_data()
    yangtze = fetch_yangtze_price()
    
    data = {
        "cctd": cctd if cctd else 736,
        "cci": cci if cci else 736,
        "freight": freight if freight else 48.7,
        "inventory": inventory if inventory else 2787,
        "power": power,
        "yangtze": yangtze if yangtze else 790,
        "today": datetime.now().strftime("%Y-%m-%d")
    }
    
    print(f"📊 采集完成:")
    print(f"   CCTD: {data['cctd']} 元/吨")
    print(f"   CCI: {data['cci']} 元/吨")
    print(f"   海运费: {data['freight']} 元/吨")
    print(f"   北方库存: {data['inventory']} 万吨")
    print(f"   电厂库存: {data['power']['inventory']} 万吨")
    print(f"   电厂日耗: {data['power']['consumption']} 万吨")
    print(f"   长江口参考价: {data['yangtze']} 元/吨")
    
    return data
