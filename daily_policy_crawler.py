import requests
import re
import time
import json
import os
from bs4 import BeautifulSoup
from datetime import datetime, timedelta
from urllib.parse import urljoin

# ==============================================
# 国家级+省级政策源（含高新/专精特新认证）
# ==============================================
TARGET_DEPARTMENTS = {
    # 国家级部门（新增）
    "工信部": {
        "base_url": "https://www.miit.gov.cn/",
        "policy_urls": ["https://www.miit.gov.cn/ztzl/zhuanjingtexin/"],  # 专精特新认证
        "keywords": ["专精特新", "小巨人企业", "专项培育"]
    },
    "科技部": {
        "base_url": "http://www.most.gov.cn/",
        "policy_urls": ["http://www.most.gov.cn/ztzl/gxqyrd/"],  # 高新企业认定
        "keywords": ["高新技术企业", "研发费用", "科技型中小企业"]
    },
    # 省级部门（保留）
    "福建省政府": {
        "base_url": "https://www.fujian.gov.cn/",
        "policy_urls": ["https://www.fujian.gov.cn/zwgk/ztzl/hqzc/"],
        "keywords": ["惠企", "专项资金", "扶持"]
    }
}

# 历史政策归档路径
HISTORICAL_POLICIES_PATH = os.path.abspath(os.path.join(
    os.getcwd(), "../public/historical_policies.json"
))
LATEST_POLICIES_PATH = os.path.abspath(os.path.join(
    os.getcwd(), "../public/policy_data.json"
))

# ==============================================
# 核心功能：抓取+归档+融合历史政策
# ==============================================
def 合规请求(url):
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/120.0.0.0 Safari/537.36"}
    try:
        response = requests.get(url, headers=headers, timeout=15)
        return response if response.status_code == 200 else None
    except:
        return None

def load_historical_policies():
    """加载历史政策备份"""
    if os.path.exists(HISTORICAL_POLICIES_PATH):
        with open(HISTORICAL_POLICIES_PATH, "r", encoding="utf-8") as f:
            return json.load(f).get("policies", [])
    return []

def save_historical_policies(new_policies):
    """合并新政策到历史归档（去重）"""
    historical = load_historical_policies()
    combined = historical + new_policies
    # 按标题去重，保留最新版本
    unique_combined = {p["title"][:50]: p for p in combined}.values()
    # 只保留近3个月政策
    three_months_ago = (datetime.now() - timedelta(days=90)).strftime("%Y-%m-%d")
    filtered = [p for p in unique_combined if p["date"] >= three_months_ago]
    with open(HISTORICAL_POLICIES_PATH, "w", encoding="utf-8") as f:
        json.dump({"update_time": datetime.now().strftime("%Y-%m-%d"), "policies": filtered}, f, ensure_ascii=False, indent=2)

def crawl_daily_policies():
    # 1. 抓取今日政策
    today_policies = []
    print("🎯 开始抓取国家级+省级政策（含高新/专精特新认证）...")
    for dept_name, config in TARGET_DEPARTMENTS.items():
        print(f"\n🔍 正在访问：{dept_name}")
        for url in config["policy_urls"]:
            response = 合规请求(url)
            if not response:
                continue
            soup = BeautifulSoup(response.text, "html.parser")
            for item in soup.find_all("li")[:30]:
                title_tag = item.find("a", href=True)
                if not title_tag:
                    continue
                title = title_tag.text.strip()
                if len(title) < 10:
                    continue
                # 关键词匹配（如"高新企业""专精特新"）
                if any(kw in title for kw in config["keywords"]):
                    date_str = re.search(r"\d{4}-\d{2}-\d{2}", item.text) or re.search(r"\d{4}年\d{2}月\d{2}日", item.text)
                    if date_str:
                        normalized_date = date_str.group().replace("年", "-").replace("月", "-").replace("日", "")
                        today_policies.append({
                            "title": title,
                            "date": normalized_date,
                            "url": urljoin(config["base_url"], title_tag["href"]),
                            "department": dept_name,
                            "type": "国家级" if dept_name in ["工信部", "科技部", "财政部"] else "省级"
                        })
                        print(f"✅ 发现政策：{title}")

    # 2. 保存今日政策+更新历史归档
    with open(LATEST_POLICIES_PATH, "w", encoding="utf-8") as f:
        json.dump({"total": len(today_policies), "policies": today_policies}, f, ensure_ascii=False, indent=2)
    save_historical_policies(today_policies)  # 合并到历史归档
    print(f"\n🎉 抓取完成！今日{len(today_policies)}条，历史归档{len(load_historical_policies())}条")
    return today_policies

if __name__ == "__main__":
    crawl_daily_policies()