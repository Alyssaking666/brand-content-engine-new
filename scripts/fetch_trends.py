"""
品牌社媒内容引擎 - 热门内容抓取脚本
使用 Apify API 抓取各平台热门内容
"""

import os
import json
from coze_workload_identity import requests

# 凭证读取
APIFY_TOKEN = os.getenv("COZE_APIFY_TOKEN_7647013926688849955")

APIFY_BASE = "https://api.apify.com/v2"

PLATFORM_ACTORS = {
    "twitter": "apidojo/twitter-scraper",
    "instagram": "apidojo/instagram-scraper",
    "tiktok": "apidojo/tiktok-scraper",
    "youtube": "apidojo/youtube-scraper",
    "facebook": "apidojo/facebook-scraper",
    "reddit": "apidojo/reddit-scraper",
}


def run_actor(actor_id, run_input):
    """启动 Apify Actor 并等待完成"""
    if not APIFY_TOKEN:
        raise ValueError("缺少 APIFY_API_TOKEN 凭证配置")

    url = f"{APIFY_BASE}/acts/{actor_id}/runs?token={APIFY_TOKEN}"
    payload = {"runInput": run_input}

    response = requests.post(url, json=payload, timeout=30)
    if response.status_code >= 400:
        raise Exception(f"启动 Actor 失败: {response.status_code}, {response.text}")

    data = response.json()
    run_id = data.get("data", {}).get("id")

    if not run_id:
        raise Exception(f"未获取到 run_id: {data}")

    # 等待运行完成
    status_url = f"{APIFY_BASE}/actor-runs/{run_id}?token={APIFY_TOKEN}"
    max_wait = 120  # 最多等120秒

    import time
    waited = 0
    while waited < max_wait:
        time.sleep(5)
        waited += 5
        status_resp = requests.get(status_url, timeout=30)
        status_data = status_resp.json().get("data", {})
        status = status_data.get("status")

        if status == "SUCCEEDED":
            default_dataset_id = status_data.get("defaultDatasetId")
            return get_dataset_items(default_dataset_id)
        elif status in ("FAILED", "ABORTED", "TIMED-OUT"):
            raise Exception(f"Actor 运行失败，状态: {status}")

    raise Exception("Actor 运行超时")


def get_dataset_items(dataset_id):
    """获取 Dataset 中的结果"""
    url = f"{APIFY_BASE}/datasets/{dataset_id}/items?token={APIFY_TOKEN}&limit=50"
    response = requests.get(url, timeout=30)
    if response.status_code >= 400:
        raise Exception(f"获取数据失败: {response.status_code}")

    return response.json()


def fetch_twitter_trends(keywords=None, max_results=10):
    """抓取 X/Twitter 热门内容"""
    run_input = {
        "searchQueries": keywords or ["trending"],
        "maxTweets": max_results,
        "sort": "Latest",
    }
    return run_actor(PLATFORM_ACTORS["twitter"], run_input)


def fetch_tiktok_trends(hashtags=None, max_results=10):
    """抓取 TikTok 热门视频"""
    run_input = {
        "hashtags": hashtags or ["trending"],
        "resultsPerPage": max_results,
        "shouldDownloadVideos": False,
    }
    return run_actor(PLATFORM_ACTORS["tiktok"], run_input)


def fetch_instagram_trends(hashtags=None, max_results=10):
    """抓取 Instagram 热门内容"""
    run_input = {
        "hashtags": hashtags or ["trending"],
        "resultsLimit": max_results,
    }
    return run_actor(PLATFORM_ACTORS["instagram"], run_input)


def fetch_youtube_trends(keywords=None, max_results=10):
    """抓取 YouTube 热门视频"""
    run_input = {
        "searchQueries": keywords or ["trending"],
        "maxResults": max_results,
    }
    return run_actor(PLATFORM_ACTORS["youtube"], run_input)


def fetch_reddit_trends(subreddits=None, max_results=10):
    """抓取 Reddit 热帖"""
    run_input = {
        "subreddits": subreddits or ["all"],
        "maxPosts": max_results,
        "sort": "hot",
    }
    return run_actor(PLATFORM_ACTORS["reddit"], run_input)


def fetch_brand_posts(platform, username, max_results=20):
    """抓取品牌主页内容（用于 brand-voice-trainer）"""
    actor_id = PLATFORM_ACTORS.get(platform)
    if not actor_id:
        raise ValueError(f"不支持的平台: {platform}")

    if platform == "instagram":
        run_input = {"usernames": [username], "resultsLimit": max_results}
    elif platform == "tiktok":
        run_input = {"profiles": [username], "resultsPerPage": max_results}
    elif platform == "twitter":
        run_input = {"handles": [username], "maxTweets": max_results}
    elif platform == "youtube":
        run_input = {"channelIds": [username], "maxResults": max_results}
    else:
        run_input = {"searchQueries": [username], "maxResults": max_results}

    return run_actor(actor_id, run_input)


if __name__ == "__main__":
    # 测试用
    print("品牌社媒内容引擎 - 热门内容抓取脚本")
    print(f"APIFY Token 配置状态: {'已配置' if APIFY_TOKEN else '未配置'}")
