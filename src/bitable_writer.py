import requests

# ============================================================
# 基础函数
# ============================================================

def get_tenant_access_token(app_id, app_secret):
    """获取飞书 tenant_access_token"""
    url = "https://open.feishu.cn/open-apis/auth/v3/tenant_access_token/internal"
    payload = {"app_id": app_id, "app_secret": app_secret}
    resp = requests.post(url, json=payload)
    return resp.json()["tenant_access_token"]


def safe_int(value, default=0):
    """安全转换为 int"""
    if value is None or value == "":
        return default
    try:
        return int(value)
    except (ValueError, TypeError):
        return default


def safe_float(value, default=0.0):
    """安全转换为 float"""
    if value is None or value == "":
        return default
    try:
        return float(value)
    except (ValueError, TypeError):
        return default


# ============================================================
# 每日预测表操作
# ============================================================

def write_prediction(app_token, table_id, token, prediction):
    """写入预测记录到多维表格"""
    url = f"https://open.feishu.cn/open-apis/bitable/v1/apps/{app_token}/tables/{table_id}/records"
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }

    fields = {
        "预测覆盖日期": prediction.get("date", ""),
        "AI预测下限": safe_int(prediction.get("lower")),
        "AI预测上限": safe_int(prediction.get("upper")),
        "置信度": prediction.get("confidence", ""),
        "市场阶段": prediction.get("market_stage", ""),
        "库存状态": prediction.get("inventory_status", ""),
        "运费周变化(%)": safe_float(prediction.get("freight_change")),
        "海运费": safe_float(prediction.get("freight")),
        "偏差归因": prediction.get("attribution", "")
    }

    payload = {"fields": fields}

    print("📤 正在写入多维表格...")
    print(f"   app_token: {app_token}")
    print(f"   table_id: {table_id}")
    print(f"   数据: {payload}")

    resp = requests.post(url, headers=headers, json=payload)
    result = resp.json()

    print(f"📥 HTTP状态码: {resp.status_code}")
    print(f"📥 API响应: {result}")

    if result.get("code") == 0:
        print("✅ 写入成功！")
    else:
        print(f"❌ 写入失败: {result.get('msg')}")

    return result


def update_actual_price(app_token, table_id, token, record_id, actual_price):
    """回填实际价格到多维表格"""
    url = f"https://open.feishu.cn/open-apis/bitable/v1/apps/{app_token}/tables/{table_id}/records/{record_id}"
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    payload = {"fields": {"实际价格": actual_price}}
    resp = requests.put(url, headers=headers, json=payload)
    return resp.json()


def get_latest_record(app_token, table_id, token):
    """获取最新一条预测记录（用于回填）"""
    url = f"https://open.feishu.cn/open-apis/bitable/v1/apps/{app_token}/tables/{table_id}/records"
    headers = {"Authorization": f"Bearer {token}"}
    params = {"page_size": 20}

    resp = requests.get(url, headers=headers, params=params)
    data = resp.json()

    if data.get("code") != 0:
        print(f"⚠️ 查询记录失败: {data}")
        return None

    items = data.get("data", {}).get("items", [])
    if not items:
        print("⚠️ 表格中没有记录")
        return None

    items_sorted = sorted(
        items,
        key=lambda x: x.get("fields", {}).get("预测覆盖日期", ""),
        reverse=True
    )

    latest = items_sorted[0]
    print(f"📋 最新记录日期: {latest['fields'].get('预测覆盖日期')}")
    return {"record_id": latest["record_id"], "fields": latest["fields"]}


def find_record_by_date(app_token, table_id, token, date_str):
    """根据预测覆盖日期查找记录"""
    url = f"https://open.feishu.cn/open-apis/bitable/v1/apps/{app_token}/tables/{table_id}/records/search"
    headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
    payload = {
        "filter": {
            "conjunction": "and",
            "conditions": [
                {"field_name": "预测覆盖日期", "operator": "is", "value": [date_str]}
            ]
        }
    }
    resp = requests.post(url, headers=headers, json=payload)
    data = resp.json()
    if data.get("code") == 0:
        items = data.get("data", {}).get("items", [])
        if items:
            return items[0]
    return None


def update_freight_change(app_token, table_id, token, record_id, change_pct):
    """更新运费周变化"""
    url = f"https://open.feishu.cn/open-apis/bitable/v1/apps/{app_token}/tables/{table_id}/records/{record_id}"
    headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
    payload = {"fields": {"运费周变化(%)": change_pct}}
    resp = requests.put(url, headers=headers, json=payload)
    return resp.json()
