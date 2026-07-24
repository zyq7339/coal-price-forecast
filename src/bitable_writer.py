import requests

def get_tenant_access_token(app_id, app_secret):
    """获取飞书 tenant_access_token"""
    url = "https://open.feishu.cn/open-apis/auth/v3/tenant_access_token/internal"
    payload = {"app_id": app_id, "app_secret": app_secret}
    resp = requests.post(url, json=payload)
    return resp.json()["tenant_access_token"]


def write_prediction(app_token, table_id, token, prediction):
    """写入预测记录到多维表格"""
    url = f"https://open.feishu.cn/open-apis/bitable/v1/apps/{app_token}/tables/{table_id}/records"
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    fields = {
        "预测覆盖日期": prediction.get("date", ""),
        "AI预测下限": int(prediction.get("lower", 0)),
        "AI预测上限": int(prediction.get("upper", 0)),
        "置信度": prediction.get("confidence", ""),
        "市场阶段": prediction.get("market_stage", ""),
        "库存状态": prediction.get("inventory_status", ""),
        "运费周变化(%)": float(prediction.get("freight_change", 0) or 0),
        "偏差归因": prediction.get("attribution", "")
    }
    payload = {"fields": fields}
    resp = requests.post(url, headers=headers, json=payload)
    return resp.json()


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
    params = {
        "page_size": 1,
        "sort": [{"field_name": "预测覆盖日期", "desc": True}]
    }
    resp = requests.get(url, headers=headers, params=params)
    data = resp.json()
    if data.get("data", {}).get("items"):
        item = data["data"]["items"][0]
        return {"record_id": item["record_id"], "fields": item["fields"]}
    return None
