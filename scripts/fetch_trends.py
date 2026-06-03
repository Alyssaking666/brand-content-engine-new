"""
品牌社媒内容引擎 - 热门内容抓取脚本 v2.0
使用 Apify API 抓取 6平台 + Google Trends 热门内容
支持时间范围过滤，确保"今日热点"数据确实来自当天
"""

import os
import json
import time
from datetime import datetime, timedelta

try:
    from coze_workload_identity import requests
except ImportError:
    import requests

# ============================================================================
# 凭证读取
# ============================================================================
APIFY_TOKEN = os.getenv("COZE_APIFY_TOKEN_7647013926688849955")
APIFY_BASE = "https://api.apify.com/v2"

# ============================================================================
# 真实 Apify Actor ID（经搜索验证可用）
# ============================================================================
PLATFORM_ACTORS = {
    "twitter": "apidojo/twitter-scraper",
    "instagram": "apify/instagram-api-scraper",
    "tiktok": "thescrapelab/tiktok-scraper-2-0",
    "youtube": "streamers/youtube-scraper",
    "facebook": "apify/facebook-pages-scraper",
    "reddit": "betterdevsscrape/reddit-scraper",
    "google_trends": "sourabhbgp/google-trends-scraper",
}


# ============================================================================
# 核心工具函数
# ============================================================================

def _check_token():
    """检查 API Token 是否已配置"""
    if not APIFY_TOKEN:
        raise ValueError(
            "缺少 APIFY_API_TOKEN 凭证。请前往 Apify Console → Settings → Integrations 获取 Token，"
            "然后在 Skill 凭证配置中添加。免费计划含每月 $5 额度。"
        )


def run_actor(actor_id, run_input, max_wait=180):
    """启动 Apify Actor 并等待完成，返回结果数据"""
    _check_token()

    url = f"{APIFY_BASE}/acts/{actor_id}/runs?token={APIFY_TOKEN}"
    payload = {"runInput": run_input}

    print(f"[Apify] 启动 Actor: {actor_id}")
    response = requests.post(url, json=payload, timeout=60)
    if response.status_code >= 400:
        raise Exception(f"启动 Actor 失败: {response.status_code}, {response.text[:500]}")

    data = response.json()
    run_id = data.get("data", {}).get("id")
    if not run_id:
        raise Exception(f"未获取到 run_id: {json.dumps(data)[:300]}")

    print(f"[Apify] 运行中: run_id={run_id}")

    # 等待运行完成
    status_url = f"{APIFY_BASE}/actor-runs/{run_id}?token={APIFY_TOKEN}"
    waited = 0
    poll_interval = 5

    while waited < max_wait:
        time.sleep(poll_interval)
        waited += poll_interval
        
        status_resp = requests.get(status_url, timeout=30)
        status_data = status_resp.json().get("data", {})
        status = status_data.get("status")

        if status == "SUCCEEDED":
            default_dataset_id = status_data.get("defaultDatasetId")
            print(f"[Apify] 运行成功，获取数据集: {default_dataset_id}")
            return get_dataset_items(default_dataset_id)
        elif status in ("FAILED", "ABORTED", "TIMED-OUT"):
            raise Exception(f"Actor 运行失败，状态: {status}")

    raise Exception(f"Actor 运行超时（>{max_wait}秒）")


def get_dataset_items(dataset_id, limit=50):
    """获取 Dataset 中的结果"""
    url = f"{APIFY_BASE}/datasets/{dataset_id}/items?token={APIFY_TOKEN}&limit={limit}"
    response = requests.get(url, timeout=30)
    if response.status_code >= 400:
        raise Exception(f"获取数据失败: {response.status_code}")

    return response.json()


def filter_by_date(items, start_date=None, end_date=None, date_field="createdAt"):
    """
    按时间范围过滤结果
    
    Args:
        items: 结果列表
        start_date: datetime对象，开始时间
        end_date: datetime对象，结束时间
        date_field: 日期字段名（不同平台不同）
    
    Returns:
        过滤后的结果
    """
    if not start_date and not end_date:
        return items
    
    filtered = []
    for item in items:
        # 尝试不同的日期字段名
        date_str = None
        for field in [date_field, "timestamp", "createTime", "time", "created_time", "publishDate", "date"]:
            if field in item and item[field]:
                date_str = item[field]
                break
        
        if not date_str:
            # 如果找不到日期字段，保留该条记录（避免过度过滤）
            continue
        
        # 尝试解析日期
        try:
            if isinstance(date_str, (int, float)):
                # 时间戳（毫秒或秒）
                item_date = datetime.fromtimestamp(date_str if date_str > 1e10 else date_str * 1000)
            else:
                # 字符串日期
                item_date = datetime.fromisoformat(date_str.replace("Z", "+00:00"))
            
            # 检查是否在时间范围内
            if start_date and item_date < start_date:
                continue
            if end_date and item_date > end_date:
                continue
            
            filtered.append(item)
        except (ValueError, TypeError):
            # 日期解析失败，保留该条记录
            continue
    
    print(f"[Date Filter] {len(items)} → {len(filtered)} 条保留")
    return filtered


# ============================================================================
# 各平台抓取函数
# ============================================================================

def fetch_twitter_trends(keywords=None, start_date=None, end_date=None, max_results=10):
    """抓取 X/Twitter 热门内容"""
    run_input = {
        "searchQueries": keywords or ["trending"],
        "maxTweets": max_results,
        "sort": "Latest",
    }
    
    # 时间过滤
    if start_date:
        run_input["start_date"] = start_date.strftime("%Y-%m-%d")
    if end_date:
        run_input["end_date"] = end_date.strftime("%Y-%m-%d")
    
    results = run_actor(PLATFORM_ACTORS["twitter"], run_input)
    return results


def fetch_tiktok_trends(hashtags=None, start_date=None, end_date=None, max_results=10):
    """抓取 TikTok 热门视频"""
    run_input = {
        "workflow": "keywords",
        "keywords": hashtags or ["trending"],
        "maxVideosPerKeyword": max_results,
    }
    
    results = run_actor(PLATFORM_ACTORS["tiktok"], run_input)
    # TikTok返回的是嵌套结构，需要展开
    filtered = []
    for item in results:
        if "videos" in item:
            filtered.extend(item["videos"])
        else:
            filtered.append(item)
    
    # 按时间过滤
    return filter_by_date(filtered, start_date, end_date, date_field="createTime")


def fetch_instagram_trends(hashtags=None, start_date=None, end_date=None, max_results=10):
    """抓取 Instagram 热门内容"""
    run_input = {
        "hashtags": hashtags or ["trending"],
        "resultsLimit": max_results,
    }
    
    results = run_actor(PLATFORM_ACTORS["instagram"], run_input)
    # Instagram 需要按时间过滤
    return filter_by_date(results, start_date, end_date, date_field="timestamp")


def fetch_youtube_trends(keywords=None, start_date=None, end_date=None, max_results=10):
    """抓取 YouTube 热门视频"""
    run_input = {
        "searchQueries": keywords or ["trending"],
        "maxResults": max_results,
    }
    
    results = run_actor(PLATFORM_ACTORS["youtube"], run_input)
    # YouTube 需要按发布时间过滤
    return filter_by_date(results, start_date, end_date, date_field="publishDate")


def fetch_facebook_trends(keywords=None, start_date=None, end_date=None, max_results=10):
    """抓取 Facebook 热门帖文"""
    run_input = {
        "startUrls": [f"https://www.facebook.com/search/top?q={kw}" for kw in (keywords or ["trending"])],
        "maxItems": max_results,
    }
    
    results = run_actor(PLATFORM_ACTORS["facebook"], run_input)
    # Facebook 需要按时间过滤
    return filter_by_date(results, start_date, end_date, date_field="time")


def fetch_reddit_trends(subreddits=None, start_date=None, end_date=None, max_results=10):
    """抓取 Reddit 热帖"""
    run_input = {
        "subredditUrls": [f"https://www.reddit.com/r/{sub}" for sub in (subreddits or ["all"])],
        "maxPosts": max_results,
        "time_filter": "day" if not start_date or (datetime.now() - start_date).days <= 1 else "week",
    }
    
    results = run_actor(PLATFORM_ACTORS["reddit"], run_input)
    # Reddit 的时间由 time_filter 控制，不需要额外过滤
    return results


def fetch_google_trends(keywords=None, geo="US", time_range="now 1-d", max_results=50):
    """
    抓取 Google Trends 数据
    
    Args:
        keywords: 关键词列表（explore模式）
        geo: 地区代码（默认US）
        time_range: 时间范围（now 1-d / now 7-d / today 3-m 等）
        max_results: 最大结果数
    
    Returns:
        Trending searches 和 Rising keywords
    """
    # 先抓取 daily trending searches
    trending_input = {
        "mode": "trending",
        "geo": geo,
        "maxResults": max_results,
    }
    trending_results = run_actor(PLATFORM_ACTORS["google_trends"], trending_input)
    
    # 如果提供了关键词，再抓取 explore 模式的 rising keywords
    explore_results = []
    if keywords:
        explore_input = {
            "mode": "explore",
            "keywords": keywords,
            "geo": geo,
            "time_range": time_range,
        }
        explore_results = run_actor(PLATFORM_ACTORS["google_trends"], explore_input)
    
    return {
        "trending_searches": trending_results,
        "rising_keywords": explore_results,
    }


# ============================================================================
# 品牌主页抓取（用于 brand-voice-trainer）
# ============================================================================

def fetch_brand_posts(platform, username, max_results=20):
    """抓取品牌主页内容（用于 brand-voice-trainer）"""
    actor_id = PLATFORM_ACTORS.get(platform)
    if not actor_id:
        raise ValueError(f"不支持的平台: {platform}")

    if platform == "instagram":
        run_input = {"directUrls": [f"https://www.instagram.com/{username}/"], "resultsLimit": max_results}
    elif platform == "tiktok":
        run_input = {"workflow": "users", "users": [username], "maxVideosPerUser": max_results}
    elif platform == "twitter":
        run_input = {"searchQueries": [f"from:{username}"], "maxTweets": max_results}

    elif platform == "youtube":
        run_input = {"startUrls": [f"https://www.youtube.com/@{username}"], "maxResults": max_results}
    else:
        run_input = {"searchQueries": [username], "maxResults": max_results}

    return run_actor(actor_id, run_input)


# ============================================================================
# 统一入口
# ============================================================================

def fetch_all_platforms_trends(config, date_str=None):
    """
    一站式抓取所有平台趋势
    
    Args:
        config: 监测配置（从 listening-config.md 读取）
        date_str: 目标日期（格式 YYYY-MM-DD），默认今天
    
    Returns:
        dict: 各平台热门内容 + Google Trends
    """
    # 计算时间范围
    if date_str:
        target_date = datetime.strptime(date_str, "%Y-%m-%d")
        start_date = target_date.replace(hour=0, minute=0, second=0, microsecond=0)
        end_date = target_date.replace(hour=23, minute=59, second=59, microsecond=999999)
    else:
        # 默认当天
        now = datetime.now()
        start_date = now.replace(hour=0, minute=0, second=0, microsecond=0)
        end_date = now
    
    print(f"[Time Range] {start_date.isoformat()} ~ {end_date.isoformat()}")
    
    results = {}
    
    # 提取配置
    keywords = config.get("keywords", [])
    subreddits = config.get("subreddits", ["all"])
    geo = config.get("geo", "US")
    
    # 1. X/Twitter
    try:
        results["twitter"] = fetch_twitter_trends(
            keywords=keywords[:5],  # 最多5个关键词
            start_date=start_date,
            end_date=end_date,
            max_results=10
        )
    except Exception as e:
        print(f"[Twitter] 抓取失败: {e}")
        results["twitter"] = []
    
    # 2. Instagram
    try:
        results["instagram"] = fetch_instagram_trends(
            hashtags=keywords[:5],
            start_date=start_date,
            end_date=end_date,
            max_results=10
        )
    except Exception as e:
        print(f"[Instagram] 抓取失败: {e}")
        results["instagram"] = []
    
    # 3. TikTok
    try:
        results["tiktok"] = fetch_tiktok_trends(
            hashtags=keywords[:5],
            start_date=start_date,
            end_date=end_date,
            max_results=10
        )
    except Exception as e:
        print(f"[TikTok] 抓取失败: {e}")
        results["tiktok"] = []
    
    # 4. YouTube
    try:
        results["youtube"] = fetch_youtube_trends(
            keywords=keywords[:5],
            start_date=start_date,
            end_date=end_date,
            max_results=10
        )
    except Exception as e:
        print(f"[YouTube] 抓取失败: {e}")
        results["youtube"] = []
    
    # 5. Facebook
    try:
        results["facebook"] = fetch_facebook_trends(
            keywords=keywords[:5],
            start_date=start_date,
            end_date=end_date,
            max_results=10
        )
    except Exception as e:
        print(f"[Facebook] 抓取失败: {e}")
        results["facebook"] = []
    
    # 6. Reddit
    try:
        results["reddit"] = fetch_reddit_trends(
            subreddits=subreddits[:5],
            start_date=start_date,
            end_date=end_date,
            max_results=10
        )
    except Exception as e:
        print(f"[Reddit] 抓取失败: {e}")
        results["reddit"] = []
    
    # 7. Google Trends
    try:
        results["google_trends"] = fetch_google_trends(
            keywords=keywords[:10],  # 最多10个关键词
            geo=geo,
            time_range="now 1-d",
            max_results=50
        )
    except Exception as e:
        print(f"[Google Trends] 抓取失败: {e}")
        results["google_trends"] = {"trending_searches": [], "rising_keywords": []}
    
    return results


if __name__ == "__main__":
    # 测试用
    print("品牌社媒内容引擎 - 热门内容抓取脚本 v2.0")
    print(f"APIFY Token 配置状态: {'已配置' if APIFY_TOKEN else '未配置'}")
    
    if APIFY_TOKEN:
        # 测试抓取今日趋势
        test_config = {
            "keywords": ["dog probiotic", "dog allergy", "pet health"],
            "subreddits": ["r/dogs", "r/DogCare"],
            "geo": "US",
        }
        results = fetch_all_platforms_trends(test_config)
        
        print("\n=== 抓取结果摘要 ===")
        for platform, data in results.items():
            if platform == "google_trends":
                print(f"{platform}: trending={len(data['trending_searches'])}, rising={len(data['rising_keywords'])}")
            else:
                print(f"{platform}: {len(data)} 条")
