"""
品牌社媒内容引擎 - 热门内容抓取脚本 v5.2
三层架构: Layer1(平台trending) + Layer2(赛道搜索) + Layer3(品牌监测)

v5.2更新:
  - 多维关键词矩阵系统: D1(产品)+D2(成分)+D3(症状)+D4(场景)
  - 平台搜索词适配: TikTok限5词, Twitter 8-10词自然语言, IG 8-10个hashtag, YouTube 8-10词问句/Review
  - 维度选用策略: D1+D3全平台; D2仅YouTube+GT; D4仅YouTube/IG/TikTok
  - 动态关键词反馈环: 从L2 Top10提取新词, 写入listening-config.md动态扩展板块
  - Reddit扩展到12个垂类subreddit + 关键词相关性过滤
  - 新增: build_platform_search_terms(), extract_new_keywords(), filter_reddit_by_keyword_relevance()
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
# 三层架构 Actor 配置
# ============================================================================

# Layer 1: 平台热门 (Platform Trending) — 使用平台原生trending API
LAYER1_ACTORS = {
    "twitter": "automation-lab/twitter-trends-scraper",
    "instagram": "agentx/instagram-trending-scraper",
    "tiktok": "coregent/tiktok-trend-discovery-scraper",
    "youtube": "streamers/youtube-scraper",
    "google_trends": "sourabhbgp/google-trends-scraper",
}

# Layer 2: 赛道相关 (Niche Relevant) — 关键词搜索, 排除品牌账号
LAYER2_ACTORS = {
    "twitter": "kaitoeasyapi/twitter-x-data-tweet-scraper-pay-per-result-cheapest",
    "instagram": "apify/instagram-hashtag-scraper",
    "tiktok": "thescrapelab/tiktok-scraper-2-0",
    "youtube": "streamers/youtube-scraper",
    "facebook": "apify/facebook-pages-scraper",
    "google_trends": "sourabhbgp/google-trends-scraper",
}

# Layer 3: 品牌动态 (Brand Monitor) — 品牌主页抓取
LAYER3_ACTORS = {
    "instagram": "apify/instagram-api-scraper",
    "tiktok": "thescrapelab/tiktok-scraper-2-0",
    "youtube": "streamers/youtube-scraper",
    "facebook": "apify/facebook-pages-scraper",
}

# ============================================================================
# 链接字段映射
# ============================================================================
PLATFORM_LINK_FIELDS = {
    "twitter": ["url", "twitterUrl", "twitterSearchUrl"],
    "instagram": ["url", "shortcode", "shortCode"],
    "tiktok": ["video_url", "webVideoUrl", "id"],
    "youtube": ["url"],
    "facebook": ["url", "postId"],
    "reddit": ["url", "permalink"],
    "google_trends": [],
}

# 品牌账号列表（用于Layer2排除）
BRAND_ACCOUNTS = {
    "instagram": ["penpenpet"],
    "tiktok": ["penpenpet"],
    "youtube": ["PenPenPet"],
    "twitter": [],
    "facebook": ["61570063181486"],
}

# ============================================================================
# 数据质量门槛（v5.1）
# ============================================================================
QUALITY_THRESHOLDS = {
    "video": {        # YouTube / TikTok / IG Reels
        "min_views": 100_000,    # 曝光≥10万
        "min_likes": 1_000,      # likes>1,000
    },
    "image": {        # IG图片 / Facebook帖文
        "min_likes": 1_000,      # likes>1,000
    },
    "tweet": {        # Twitter/X
        "min_likes": 500,        # likes>500
    },
    "reddit": {       # Reddit帖子
        "min_upvotes": 50,       # upvotes>50
        "min_comments": 20,      # 评论>20
    },
}

# Reddit 垂类 Subreddit 列表（v5.2扩展到12个，可从listening-config.md覆盖）
DEFAULT_SUBREDDITS = [
    # 核心养狗
    "dogs", "DogCare", "puppy101",
    # 狗健康
    "DogHealth", "AskVet", "DogAllergies",
    # 狗粮/营养
    "dogfood", "rawpetfood",
    # 综合宠物
    "pets", "PetHealth",
    # 生活方式
    "seniordogs", "reactivedogs",
    # 自然/整全
    "NaturalPetCare",
]


# ============================================================================
# 多维关键词矩阵（v5.2 核心升级）
# ============================================================================

# 关键词维度定义 — 具体词汇从 listening-config.md 读取，以下为默认值
KEYWORD_DIMENSIONS = {
    "D1_product": [
        "dog probiotic", "dog supplement", "joint chews", "allergy chews",
        "calming treats", "dental chews", "hip and joint", "multivitamin dogs",
    ],
    "D2_ingredient": [
        "glucosamine dogs", "fish oil dogs", "turmeric pet",
        "omega 3 dogs", "prebiotic dogs", "collagen dogs", "digestive enzymes dogs",
    ],
    "D3_symptom": [
        "dog itchy skin", "dog diarrhea", "dog joint pain", "senior dog mobility",
        "dog upset stomach", "dog hair loss", "dog bad breath", "dog anxiety",
        "dog hot spots", "dog scratching", "dog sensitive stomach",
    ],
    "D4_scenario": [
        "dog wellness routine", "aging dog care", "rescue dog nutrition",
        "new puppy essentials", "senior dog quality of life", "dog preventive health",
    ],
}

# 平台维度优先级 & 搜索词数量限制
PLATFORM_KEYWORD_CONFIG = {
    "tiktok": {"priority": ["D3_symptom", "D1_product", "D4_scenario"], "max_keywords": 5},
    "instagram": {"priority": ["D1_product", "D4_scenario", "D3_symptom"], "max_keywords": 10},
    "youtube": {"priority": ["D1_product", "D3_symptom", "D2_ingredient", "D4_scenario"], "max_keywords": 10},
    "twitter": {"priority": ["D3_symptom", "D1_product", "D4_scenario"], "max_keywords": 10},
    "google_trends": {"priority": ["D1_product", "D2_ingredient", "D3_symptom"], "max_keywords": 8},
    "reddit": {"priority": ["D3_symptom", "D1_product", "D4_scenario"], "max_keywords": 0},  # subreddit驱动
}


def build_platform_search_terms(platform, config_keywords=None, dynamic_keywords=None):
    """
    根据平台维度优先级和格式要求，组装该平台的搜索词组

    Args:
        platform: 平台标识 (tiktok/instagram/youtube/twitter/google_trends/reddit)
        config_keywords: 从 listening-config.md 读取的关键词矩阵(覆盖默认)
        dynamic_keywords: 从 listening-config.md 动态扩展板块读取的词

    Returns:
        list: 该平台的搜索词列表
    """
    kw_dims = config_keywords or KEYWORD_DIMENSIONS
    platform_config = PLATFORM_KEYWORD_CONFIG.get(platform, {})
    priority = platform_config.get("priority", ["D1_product"])
    max_kw = platform_config.get("max_keywords", 8)

    # 按维度优先级收集搜索词
    search_terms = []
    for dim_key in priority:
        dim_words = kw_dims.get(dim_key, [])
        search_terms.extend(dim_words)

    # 追加动态扩展关键词
    if dynamic_keywords:
        search_terms.extend(dynamic_keywords)

    # 去重
    seen = set()
    unique_terms = []
    for term in search_terms:
        term_lower = term.lower()
        if term_lower not in seen:
            seen.add(term_lower)
            unique_terms.append(term)
        if len(unique_terms) >= max_kw:
            break

    # 平台格式适配
    if platform == "instagram":
        # IG用hashtag格式: 去掉空格和特殊字符
        formatted = []
        for term in unique_terms:
            tag = term.replace(" ", "").replace("#", "").replace('"', "")
            formatted.append(tag)
        return formatted

    if platform == "youtube":
        # YouTube适配: 部分词加review/问句格式
        formatted = []
        for term in unique_terms:
            if term in kw_dims.get("D1_product", []):
                formatted.append(f"best {term} review")
            elif term in kw_dims.get("D2_ingredient", []):
                formatted.append(f"is {term} good for dogs")
            else:
                formatted.append(term)
        return formatted

    return unique_terms


def _check_token():
    if not APIFY_TOKEN:
        raise ValueError("缺少 APIFY_API_TOKEN 凭证")


def extract_link(platform, item):
    """从Apify返回数据中提取平台链接"""
    link_fields = PLATFORM_LINK_FIELDS.get(platform, [])
    for field in link_fields:
        val = item.get(field)
        if val:
            if platform == "tiktok" and field == "id":
                return f"https://www.tiktok.com/video/{val}"
            if platform == "instagram" and field in ("shortcode", "shortCode"):
                return f"https://www.instagram.com/p/{val}/"
            if platform == "facebook" and field == "postId":
                return f"https://www.facebook.com/{val}"
            if platform == "reddit" and field == "permalink":
                return f"https://www.reddit.com{val}"
            if isinstance(val, str) and val.startswith("http"):
                return val
    return None


def is_brand_content(platform, item):
    """检查是否为品牌自身内容（Layer2需排除）"""
    brand_accounts = BRAND_ACCOUNTS.get(platform, [])
    if not brand_accounts:
        return False

    author_fields = {
        "twitter": ["author", "user", "userName"],
        "instagram": ["ownerUsername", "username"],
        "tiktok": ["authorName"],
        "youtube": ["channelName", "channelTitle"],
        "facebook": ["username", "pageId"],
    }

    for field in author_fields.get(platform, []):
        val = item.get(field, "")
        if val and str(val).lower() in [a.lower() for a in brand_accounts]:
            return True

    # 检查嵌套author对象
    if "author" in item and isinstance(item["author"], dict):
        for key in ["userName", "username", "nickname", "uniqueId"]:
            val = item["author"].get(key, "")
            if val and str(val).lower() in [a.lower() for a in brand_accounts]:
                return True

    return False


def run_actor(actor_id, run_input, max_wait=180):
    """启动 Apify Actor 并等待完成，返回结果数据"""
    _check_token()
    url = f"{APIFY_BASE}/acts/{actor_id}/runs?token={APIFY_TOKEN}"

    print(f"[Apify] 启动 Actor: {actor_id}")
    response = requests.post(url, json=run_input, timeout=60)
    if response.status_code >= 400:
        raise Exception(f"启动 Actor 失败: {response.status_code}, {response.text[:500]}")

    data = response.json()
    run_id = data.get("data", {}).get("id")
    if not run_id:
        raise Exception(f"未获取到 run_id: {json.dumps(data)[:300]}")

    print(f"[Apify] 运行中: run_id={run_id}")
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
    """按时间范围过滤结果"""
    if not start_date and not end_date:
        return items

    filtered = []
    for item in items:
        date_str = None
        for field in [date_field, "timestamp", "createTime", "create_time", "time",
                      "created_time", "publishDate", "publishedAt", "date"]:
            if field in item and item[field]:
                date_str = item[field]
                break

        if not date_str:
            continue

        try:
            if isinstance(date_str, (int, float)):
                item_date = datetime.fromtimestamp(date_str if date_str > 1e10 else date_str)
            else:
                item_date = datetime.fromisoformat(date_str.replace("Z", "+00:00"))

            if start_date and item_date < start_date:
                continue
            if end_date and item_date > end_date:
                continue

            filtered.append(item)
        except (ValueError, TypeError):
            continue

    print(f"[Date Filter] {len(items)} → {len(filtered)} 条保留")
    return filtered


# ============================================================================
# 数据质量门槛过滤（v5.1）
# ============================================================================

def calculate_engagement_rate(item, platform):
    """计算互动率 = (likes + comments + shares) / views × 100%"""
    views = 0
    likes = 0
    comments = 0
    shares = 0

    if platform in ("youtube",):
        views = item.get("viewCount", 0) or 0
        likes = item.get("numberOfLikes", 0) or 0
        comments = item.get("numberOfComments", 0) or 0
    elif platform in ("tiktok",):
        stats = item.get("statsV2", {})
        views = stats.get("playCount", 0) or item.get("playCount", 0) or 0
        likes = stats.get("diggCount", 0) or item.get("diggCount", 0) or 0
        comments = stats.get("commentCount", 0) or item.get("commentCount", 0) or 0
        shares = stats.get("shareCount", 0) or item.get("shareCount", 0) or 0
    elif platform in ("instagram",):
        views = item.get("videoViewCount", 0) or item.get("playCount", 0) or 0
        likes = item.get("likesCount", 0) or 0
        comments = item.get("commentsCount", 0) or 0

    if views > 0:
        return round((likes + comments + shares) / views * 100, 2)
    return 0


def meets_quality_threshold(item, platform, content_type=None):
    """
    检查内容是否达到数据质量门槛（v5.1）
    
    Args:
        item: 单条内容数据
        platform: 平台标识 (youtube/tiktok/instagram/twitter/facebook/reddit)
        content_type: 内容类型 (video/image/tweet/reddit)，如不指定则自动判断
    
    Returns:
        tuple: (是否达标, 门槛详情dict)
    """
    # 自动判断内容类型
    if content_type is None:
        if platform == "twitter":
            content_type = "tweet"
        elif platform == "reddit":
            content_type = "reddit"
        elif platform in ("youtube", "tiktok"):
            content_type = "video"
        elif platform == "instagram":
            # IG: 有视频播放量则是视频，否则是图片
            has_video = bool(item.get("videoViewCount") or item.get("playCount") or item.get("isVideo"))
            content_type = "video" if has_video else "image"
        elif platform == "facebook":
            content_type = "image"  # Facebook帖文统一按图片类门槛
        else:
            content_type = "image"

    threshold = QUALITY_THRESHOLDS.get(content_type, {})
    details = {"content_type": content_type, "threshold": threshold, "passed": True, "reason": ""}

    if content_type == "video":
        views = 0
        likes = 0
        if platform == "youtube":
            views = item.get("viewCount", 0) or 0
            likes = item.get("numberOfLikes", 0) or 0
        elif platform == "tiktok":
            stats = item.get("statsV2", {})
            views = stats.get("playCount", 0) or item.get("playCount", 0) or 0
            likes = stats.get("diggCount", 0) or item.get("diggCount", 0) or 0
        elif platform == "instagram":
            views = item.get("videoViewCount", 0) or item.get("playCount", 0) or 0
            likes = item.get("likesCount", 0) or 0

        if views < threshold.get("min_views", 0):
            details["passed"] = False
            details["reason"] = f"曝光{views}<{threshold['min_views']}"
        if likes < threshold.get("min_likes", 0):
            details["passed"] = False
            details["reason"] += f" likes{likes}<{threshold['min_likes']}" if details["reason"] else f"likes{likes}<{threshold['min_likes']}"

    elif content_type == "image":
        likes = item.get("likesCount", 0) or item.get("likes", 0) or 0
        if likes < threshold.get("min_likes", 0):
            details["passed"] = False
            details["reason"] = f"likes{likes}<{threshold['min_likes']}"

    elif content_type == "tweet":
        likes = item.get("likeCount", 0) or item.get("likes", 0) or 0
        if likes < threshold.get("min_likes", 0):
            details["passed"] = False
            details["reason"] = f"likes{likes}<{threshold['min_likes']}"

    elif content_type == "reddit":
        upvotes = item.get("score", 0) or 0
        comments = item.get("num_comments", 0) or 0
        if upvotes < threshold.get("min_upvotes", 0):
            details["passed"] = False
            details["reason"] = f"upvotes{upvotes}<{threshold['min_upvotes']}"
        if comments < threshold.get("min_comments", 0):
            details["passed"] = False
            details["reason"] += f" comments{comments}<{threshold['min_comments']}" if details["reason"] else f"comments{comments}<{threshold['min_comments']}"

    return details["passed"], details


def filter_by_quality(items, platform, content_type=None):
    """按数据质量门槛过滤，返回 (达标列表, 未达标列表)"""
    passed = []
    below = []
    for item in items:
        ok, details = meets_quality_threshold(item, platform, content_type)
        item["_quality"] = details
        if ok:
            passed.append(item)
        else:
            below.append(item)
    print(f"[Quality Filter {platform}] {len(items)} → {len(passed)} 达标, {len(below)} 低于门槛")
    return passed, below


# ============================================================================
# Reddit Public JSON API（v5.1 — 垂类subreddit直连）
# ============================================================================

def fetch_reddit_hot(subreddit, limit=25):
    """
    获取subreddit的热门帖文
    API: https://www.reddit.com/r/{subreddit}/hot.json?limit=25
    """
    url = f"https://www.reddit.com/r/{subreddit}/hot.json?limit={limit}"
    headers = {"User-Agent": "BrandContentEngine/5.1"}
    try:
        resp = requests.get(url, headers=headers, timeout=15)
        if resp.status_code == 200:
            data = resp.json()
            posts = []
            for child in data.get("data", {}).get("children", []):
                post = child.get("data", {})
                posts.append({
                    "title": post.get("title", ""),
                    "url": post.get("url", ""),
                    "permalink": f"https://www.reddit.com{post.get('permalink', '')}",
                    "score": post.get("score", 0),
                    "num_comments": post.get("num_comments", 0),
                    "subreddit": post.get("subreddit", subreddit),
                    "created_utc": post.get("created_utc", 0),
                    "selftext": (post.get("selftext", "") or "")[:300],
                    "author": post.get("author", ""),
                    "link_flair_text": post.get("link_flair_text", ""),
                })
            print(f"[Reddit] r/{subreddit} hot: {len(posts)} 条")
            return posts
        else:
            print(f"[Reddit] r/{subreddit} hot 请求失败: {resp.status_code}")
            return []
    except Exception as e:
        print(f"[Reddit] r/{subreddit} hot 异常: {e}")
        return []


def fetch_reddit_top_month(subreddit, limit=25):
    """
    获取subreddit当月Top帖文
    API: https://www.reddit.com/r/{subreddit}/top.json?t=month&limit=25
    """
    url = f"https://www.reddit.com/r/{subreddit}/top.json?t=month&limit={limit}"
    headers = {"User-Agent": "BrandContentEngine/5.1"}
    try:
        resp = requests.get(url, headers=headers, timeout=15)
        if resp.status_code == 200:
            data = resp.json()
            posts = []
            for child in data.get("data", {}).get("children", []):
                post = child.get("data", {})
                posts.append({
                    "title": post.get("title", ""),
                    "url": post.get("url", ""),
                    "permalink": f"https://www.reddit.com{post.get('permalink', '')}",
                    "score": post.get("score", 0),
                    "num_comments": post.get("num_comments", 0),
                    "subreddit": post.get("subreddit", subreddit),
                    "created_utc": post.get("created_utc", 0),
                    "selftext": (post.get("selftext", "") or "")[:300],
                    "author": post.get("author", ""),
                    "link_flair_text": post.get("link_flair_text", ""),
                })
            print(f"[Reddit] r/{subreddit} top/month: {len(posts)} 条")
            return posts
        else:
            print(f"[Reddit] r/{subreddit} top/month 请求失败: {resp.status_code}")
            return []
    except Exception as e:
        print(f"[Reddit] r/{subreddit} top/month 异常: {e}")
        return []


def fetch_reddit_niche(subreddits=None, min_upvotes=50, min_comments=20, top_n=10, keyword_dims=None):
    """
    Reddit垂类社区抓取（v5.2）
    - 只抓垂类subreddit（非r/all）
    - 合并hot + top(month)后去重
    - 关键词相关性过滤（v5.2新增）：标题/正文需包含D1-D4维度关键词
    - 过滤: upvotes>{min_upvotes} 且 评论>{min_comments}
    - 按互动量排序取Top {top_n}
    """
    subreddits = subreddits or DEFAULT_SUBREDDITS
    kw_dims = keyword_dims or KEYWORD_DIMENSIONS
    all_posts = []
    seen_ids = set()

    # 构建关键词匹配池（D1-D4所有词的小写集合）
    keyword_pool = set()
    for dim_key in ["D1_product", "D2_ingredient", "D3_symptom", "D4_scenario"]:
        for word in kw_dims.get(dim_key, []):
            keyword_pool.add(word.lower())

    for sub in subreddits:
        # 抓取hot
        hot_posts = fetch_reddit_hot(sub)
        # 抓取top(month)
        top_posts = fetch_reddit_top_month(sub)

        for post in hot_posts + top_posts:
            # 去重（用permalink做唯一标识）
            post_id = post.get("permalink", "")
            if post_id in seen_ids:
                continue
            seen_ids.add(post_id)

            # 质量门槛过滤
            score = post.get("score", 0)
            comments = post.get("num_comments", 0)
            if score <= min_upvotes or comments <= min_comments:
                continue

            # 关键词相关性过滤（v5.2新增）
            if not _reddit_post_matches_keywords(post, keyword_pool):
                continue

            post["_quality"] = {"passed": True, "content_type": "reddit"}
            all_posts.append(post)

    # 按互动量排序（score + num_comments 加权）
    all_posts.sort(key=lambda x: x.get("score", 0) + x.get("num_comments", 0) * 2, reverse=True)

    print(f"[Reddit Niche] {len(subreddits)} 个subreddit → {len(all_posts)} 条达标 → Top {top_n}")
    return all_posts[:top_n]


def _reddit_post_matches_keywords(post, keyword_pool):
    """
    检查Reddit帖子标题或正文是否包含D1-D4维度关键词（宽松匹配）
    如果keyword_pool为空则跳过过滤（兼容旧模式）
    """
    if not keyword_pool:
        return True

    title = (post.get("title", "") or "").lower()
    selftext = (post.get("selftext", "") or "").lower()
    combined = f"{title} {selftext}"

    for keyword in keyword_pool:
        # 宽松匹配：关键词的每个词都出现在文本中
        words = keyword.split()
        if all(w in combined for w in words):
            return True

    return False


# ============================================================================
# Layer 1: 平台热门 (Platform Trending)
# ============================================================================

def fetch_layer1_twitter(locations=None, max_items=100):
    """
    Layer 1: Twitter平台trending topics
    Actor: automation-lab/twitter-trends-scraper
    输出: trending topic名称 + 推文量 + 搜索URL
    """
    run_input = {
        "locations": locations or ["United States", "Worldwide"],
        "maxItems": max_items,
    }
    results = run_actor(LAYER1_ACTORS["twitter"], run_input)
    for r in results:
        r["_extracted_link"] = extract_link("twitter", r)
        r["_layer"] = "L1_trending"
    return results


def fetch_layer1_instagram(max_results=50):
    """
    Layer 1: Instagram Explore trending内容
    Actor: agentx/instagram-trending-scraper
    输出: trending帖子 + topic标签(section/topic)
    """
    run_input = {
        "max_results": max_results,
        "download_medias": "none",
    }
    results = run_actor(LAYER1_ACTORS["instagram"], run_input)
    for r in results:
        r["_extracted_link"] = extract_link("instagram", r)
        r["_layer"] = "L1_trending"
    return results


def fetch_layer1_tiktok():
    """
    Layer 1: TikTok trending + discovery数据
    Actor: coregent/tiktok-trend-discovery-scraper
    """
    results = run_actor(LAYER1_ACTORS["tiktok"], {})
    for r in results:
        r["_extracted_link"] = extract_link("tiktok", r)
        r["_layer"] = "L1_trending"
    return results


def fetch_layer1_youtube(search_queries=None, max_results=15):
    """
    Layer 1: YouTube trending搜索（近似方案，无直接trending API）
    Actor: streamers/youtube-scraper
    """
    run_input = {
        "searchQueries": search_queries or ["trending pets today", "viral dog video", "trending animals"],
        "maxResults": max_results,
    }
    results = run_actor(LAYER1_ACTORS["youtube"], run_input)
    for r in results:
        r["_extracted_link"] = extract_link("youtube", r)
        r["_layer"] = "L1_trending"
    return results


def fetch_layer1_google_trends(geo="US", max_results=50):
    """
    Layer 1: Google Trends trending searches
    Actor: sourabhbgp/google-trends-scraper
    """
    run_input = {"mode": "trending", "geo": geo, "maxResults": max_results}
    return run_actor(LAYER1_ACTORS["google_trends"], run_input)


# ============================================================================
# Layer 2: 赛道相关 (Niche Relevant) — 排除品牌内容
# ============================================================================

def fetch_layer2_twitter(search_terms, start_date=None, end_date=None, max_tweets=20):
    """
    Layer 2: Twitter赛道关键词搜索（无最低限制）
    Actor: kaitoeasyapi/twitter-x-data-tweet-scraper-pay-per-result-cheapest
    自动排除品牌账号内容
    """
    # 嵌入日期过滤
    if start_date:
        dated_terms = [f"{t} since:{start_date.strftime('%Y-%m-%d')}" for t in search_terms]
    else:
        dated_terms = search_terms

    run_input = {
        "searchTerms": dated_terms,
        "maxTweets": max_tweets,
        "sort": "Top",
    }
    results = run_actor(LAYER2_ACTORS["twitter"], run_input)

    # 排除品牌内容
    filtered = [r for r in results if not is_brand_content("twitter", r)]
    print(f"[Layer2 Twitter] {len(results)} → {len(filtered)} 条（排除品牌后）")

    for r in filtered:
        r["_extracted_link"] = extract_link("twitter", r)
        r["_layer"] = "L2_niche"
    return filtered


def fetch_layer2_instagram(hashtags, max_results=20):
    """
    Layer 2: Instagram hashtag搜索（非品牌主页）
    Actor: apify/instagram-hashtag-scraper
    自动排除品牌账号内容
    """
    run_input = {
        "hashtags": hashtags,
        "resultsLimit": max_results,
    }
    results = run_actor(LAYER2_ACTORS["instagram"], run_input)

    # 排除品牌内容
    filtered = [r for r in results if not is_brand_content("instagram", r)]
    print(f"[Layer2 Instagram] {len(results)} → {len(filtered)} 条（排除品牌后）")

    for r in filtered:
        r["_extracted_link"] = extract_link("instagram", r)
        r["_layer"] = "L2_niche"
    return filtered


def fetch_layer2_tiktok(keywords, start_date=None, end_date=None, max_videos=10):
    """
    Layer 2: TikTok赛道关键词搜索
    Actor: thescrapelab/tiktok-scraper-2-0
    自动排除品牌账号内容
    """
    run_input = {
        "workflow": "keywords",
        "keywords": keywords,
        "maxVideosPerKeyword": max_videos,
    }
    results = run_actor(LAYER2_ACTORS["tiktok"], run_input)

    # 展开嵌套结构
    flat = []
    for item in results:
        if isinstance(item, dict) and "videos" in item:
            flat.extend(item["videos"])
        elif isinstance(item, dict):
            flat.append(item)

    # 时间过滤
    filtered = filter_by_date(flat, start_date, end_date, date_field="createTime")

    # 排除品牌内容
    niche_filtered = [r for r in filtered if not is_brand_content("tiktok", r)]
    print(f"[Layer2 TikTok] {len(filtered)} → {len(niche_filtered)} 条（排除品牌后）")

    for r in niche_filtered:
        r["_extracted_link"] = extract_link("tiktok", r)
        r["_layer"] = "L2_niche"
    return niche_filtered


def fetch_layer2_youtube(search_queries, start_date=None, end_date=None, max_results=15):
    """
    Layer 2: YouTube赛道关键词搜索
    自动排除品牌频道
    """
    run_input = {
        "searchQueries": search_queries,
        "maxResults": max_results,
    }
    results = run_actor(LAYER2_ACTORS["youtube"], run_input)

    filtered = filter_by_date(results, start_date, end_date, date_field="publishedAt")

    # 排除品牌频道
    niche_filtered = [r for r in filtered if not is_brand_content("youtube", r)]
    print(f"[Layer2 YouTube] {len(filtered)} → {len(niche_filtered)} 条（排除品牌后）")

    for r in niche_filtered:
        r["_extracted_link"] = extract_link("youtube", r)
        r["_layer"] = "L2_niche"
    return niche_filtered


def fetch_layer2_facebook(page_urls, max_items=10):
    """
    Layer 2: Facebook指定竞品/行业品牌主页监测
    排除品牌主页
    """
    run_input = {
        "startUrls": [{"url": u} for u in page_urls],
        "maxItems": max_items,
    }
    results = run_actor(LAYER2_ACTORS["facebook"], run_input)

    niche_filtered = [r for r in results if not is_brand_content("facebook", r)]
    print(f"[Layer2 Facebook] {len(results)} → {len(niche_filtered)} 条（排除品牌后）")

    for r in niche_filtered:
        r["_extracted_link"] = extract_link("facebook", r)
        r["_layer"] = "L2_niche"
    return niche_filtered


def fetch_layer2_google_trends(keywords, geo="US", time_range="now 1-d"):
    """
    Layer 2: Google Trends explore模式（赛道关键词Rising queries）
    """
    run_input = {
        "mode": "explore",
        "searchTerms": keywords[:10],
        "geo": geo,
        "time_range": time_range,
    }
    try:
        return run_actor(LAYER2_ACTORS["google_trends"], run_input)
    except Exception as e:
        print(f"[Layer2 Google Trends] 失败: {e}")
        return []


# ============================================================================
# Layer 3: 品牌动态 (Brand Monitor)
# ============================================================================

def fetch_layer3_brand_monitor(brand_urls, max_results=10):
    """
    Layer 3: 品牌社媒主页最新内容监测
    """
    results = {}

    # Instagram
    if "instagram" in brand_urls:
        try:
            run_input = {
                "directUrls": [brand_urls["instagram"]],
                "resultsLimit": max_results,
            }
            ig_results = run_actor(LAYER3_ACTORS["instagram"], run_input)
            for r in ig_results:
                r["_extracted_link"] = extract_link("instagram", r)
                r["_layer"] = "L3_brand"
            results["instagram"] = ig_results
        except Exception as e:
            print(f"[Layer3 Instagram] 失败: {e}")
            results["instagram"] = []

    # TikTok
    if "tiktok" in brand_urls:
        try:
            run_input = {
                "workflow": "profiles",
                "profiles": [brand_urls["tiktok"]],
                "maxVideosPerProfile": max_results,
            }
            tt_results = run_actor(LAYER3_ACTORS["tiktok"], run_input)
            for r in tt_results:
                r["_extracted_link"] = extract_link("tiktok", r)
                r["_layer"] = "L3_brand"
            results["tiktok"] = tt_results
        except Exception as e:
            print(f"[Layer3 TikTok] 失败: {e}")
            results["tiktok"] = []

    # YouTube
    if "youtube" in brand_urls:
        try:
            run_input = {
                "searchQueries": [brand_urls["youtube"]],
                "maxResults": max_results,
            }
            yt_results = run_actor(LAYER3_ACTORS["youtube"], run_input)
            for r in yt_results:
                r["_extracted_link"] = extract_link("youtube", r)
                r["_layer"] = "L3_brand"
            results["youtube"] = yt_results
        except Exception as e:
            print(f"[Layer3 YouTube] 失败: {e}")
            results["youtube"] = []

    # Facebook
    if "facebook" in brand_urls:
        try:
            run_input = {
                "startUrls": [{"url": brand_urls["facebook"]}],
                "maxItems": max_results,
            }
            fb_results = run_actor(LAYER3_ACTORS["facebook"], run_input)
            for r in fb_results:
                r["_extracted_link"] = extract_link("facebook", r)
                r["_layer"] = "L3_brand"
            results["facebook"] = fb_results
        except Exception as e:
            print(f"[Layer3 Facebook] 失败: {e}")
            results["facebook"] = []

    return results


# ============================================================================
# Reddit 降级处理
# ============================================================================

def extract_new_keywords(layer2_top_items, existing_keywords=None, min_occurrence=3):
    """
    从Layer 2 Top 10结果中提取新关键词（v5.2动态关键词反馈环）
    
    提取规则:
    1. 高频出现的新hashtag（出现≥3次且不在现有词库中）
    2. 新发现的竞品品牌名（暂未实现，需外部品牌库）

    Args:
        layer2_top_items: Layer 2各平台的Top10结果列表 dict[platform -> list]
        existing_keywords: 现有关键词集合（用于去重），从listening-config.md读取
        min_occurrence: hashtag最低出现次数

    Returns:
        list[dict]: 新发现关键词列表，格式: [{"keyword": str, "platform": str, "count": int}]
    """
    if not existing_keywords:
        existing_keywords = set()
    else:
        existing_keywords = {k.lower() for k in existing_keywords}

    hashtag_counter = {}  # hashtag -> {count, platforms}

    for platform, items in layer2_top_items.items():
        for item in items:
            # 从caption/text/title中提取hashtag
            text_fields = []
            for field in ["caption", "text", "title", "description"]:
                val = item.get(field, "")
                if val:
                    text_fields.append(str(val))

            full_text = " ".join(text_fields)

            # 提取hashtag（#开头的词）
            import re
            hashtags = re.findall(r'#(\w+)', full_text)
            for tag in hashtags:
                tag_lower = tag.lower()
                if tag_lower not in existing_keywords:
                    if tag_lower not in hashtag_counter:
                        hashtag_counter[tag_lower] = {"count": 0, "platforms": set()}
                    hashtag_counter[tag_lower]["count"] += 1
                    hashtag_counter[tag_lower]["platforms"].add(platform)

    # 筛选出现≥min_occurrence次的新hashtag
    new_keywords = []
    for tag, info in hashtag_counter.items():
        if info["count"] >= min_occurrence:
            new_keywords.append({
                "keyword": f"#{tag}",
                "platform": "/".join(sorted(info["platforms"])),
                "count": info["count"],
            })

    # 按出现次数降序排列
    new_keywords.sort(key=lambda x: x["count"], reverse=True)

    print(f"[Dynamic Keywords] 从L2 Top10中提取 {len(new_keywords)} 个新关键词")
    return new_keywords


def fetch_reddit_data_degraded(keywords, time_filter="day"):
    """
    Reddit降级模式: 环境无法访问reddit.com时使用搜索补充
    优先使用 fetch_reddit_niche() 直连Public JSON API
    """
    try:
        niche_posts = fetch_reddit_niche()
        if niche_posts:
            return {
                "status": "ok",
                "source": "public_json_api",
                "data": niche_posts,
            }
    except Exception as e:
        print(f"[Reddit] Public JSON API失败: {e}")

    # 降级为搜索补充
    print("[Reddit] 降级为搜索补充模式")
    return {
        "status": "degraded",
        "reason": "环境无法访问reddit.com Public JSON API",
        "fallback": "使用搜索工具搜索 site:reddit.com + 赛道关键词",
        "data": [],
    }


# ============================================================================
# 统一入口
# ============================================================================

def fetch_all_platforms_trends(config, date_str=None, include_brand=False):
    """
    三层架构一站式抓取（v5.2 多维关键词矩阵驱动）

    Args:
        config: 监测配置（从 listening-config.md 读取），含:
            - keywords: 关键词矩阵 {D1_product: [...], D2_ingredient: [...], D3_symptom: [...], D4_scenario: [...]}
            - dynamic_keywords: 动态扩展关键词列表
            - subreddits: Reddit subreddit列表
            - hashtags: IG hashtag列表（如不提供则从矩阵生成）
            - geo: Google Trends地区
            - facebook_competitor_pages: Facebook竞品页面URL
            - brand_urls: 品牌主页URL
        date_str: 目标日期（格式 YYYY-MM-DD），默认今天
        include_brand: 是否包含Layer3品牌动态

    Returns:
        dict: {
            layer1: {platform: [items]},
            layer2: {platform: [items]},
            layer3: {platform: [items]},
            google_trends: {...},
            reddit: {...},
            new_keywords: [...],  # v5.2 动态关键词提取结果
        }
    """
    if date_str:
        target_date = datetime.strptime(date_str, "%Y-%m-%d")
        start_date = target_date.replace(hour=0, minute=0, second=0, microsecond=0)
        end_date = target_date.replace(hour=23, minute=59, second=59, microsecond=999999)
    else:
        now = datetime.now()
        start_date = now.replace(hour=0, minute=0, second=0, microsecond=0)
        end_date = now

    print(f"[Time Range] {start_date.isoformat()} ~ {end_date.isoformat()}")

    # 读取关键词矩阵（优先用config中的，否则用默认）
    kw_dims = config.get("keywords", KEYWORD_DIMENSIONS)
    dynamic_kw = config.get("dynamic_keywords", [])
    subreddits = config.get("subreddits", DEFAULT_SUBREDDITS)
    geo = config.get("geo", "US")

    # 为每个平台组装搜索词
    twitter_terms = build_platform_search_terms("twitter", kw_dims, dynamic_kw)
    instagram_hashtags = config.get("hashtags") or build_platform_search_terms("instagram", kw_dims, dynamic_kw)
    tiktok_terms = build_platform_search_terms("tiktok", kw_dims, dynamic_kw)
    youtube_terms = build_platform_search_terms("youtube", kw_dims, dynamic_kw)
    gt_terms = build_platform_search_terms("google_trends", kw_dims, dynamic_kw)

    print(f"[Keywords] Twitter: {len(twitter_terms)} | IG: {len(instagram_hashtags)} | TikTok: {len(tiktok_terms)} | YouTube: {len(youtube_terms)} | GT: {len(gt_terms)}")

    results = {"layer1": {}, "layer2": {}, "layer3": {}, "google_trends": {}, "reddit": {}, "new_keywords": []}

    # ---- Layer 1: 平台热门 ----
    layer1_fns = {
        "twitter": lambda: fetch_layer1_twitter(),
        "instagram": lambda: fetch_layer1_instagram(),
        "tiktok": lambda: fetch_layer1_tiktok(),
        "youtube": lambda: fetch_layer1_youtube(),
    }
    for platform, fn in layer1_fns.items():
        try:
            results["layer1"][platform] = fn()
        except Exception as e:
            print(f"[Layer1 {platform}] 失败: {e}")
            results["layer1"][platform] = []

    # ---- Layer 2: 赛道相关（多维关键词矩阵驱动） ----
    layer2_fns = {
        "twitter": lambda: fetch_layer2_twitter(twitter_terms, start_date, end_date, max_tweets=10),
        "instagram": lambda: fetch_layer2_instagram(instagram_hashtags, max_results=15),
        "tiktok": lambda: fetch_layer2_tiktok(tiktok_terms, start_date, end_date, max_videos=5),
        "youtube": lambda: fetch_layer2_youtube(youtube_terms, start_date, end_date, max_results=10),
    }
    for platform, fn in layer2_fns.items():
        try:
            results["layer2"][platform] = fn()
        except Exception as e:
            print(f"[Layer2 {platform}] 失败: {e}")
            results["layer2"][platform] = []

    # Facebook Layer2 (需配置竞品主页URL)
    fb_pages = config.get("facebook_competitor_pages", [])
    if fb_pages:
        try:
            results["layer2"]["facebook"] = fetch_layer2_facebook(fb_pages)
        except Exception as e:
            print(f"[Layer2 Facebook] 失败: {e}")
            results["layer2"]["facebook"] = []

    # ---- Layer 3: 品牌动态 (可选) ----
    if include_brand:
        brand_urls = config.get("brand_urls", {})
        try:
            results["layer3"] = fetch_layer3_brand_monitor(brand_urls)
        except Exception as e:
            print(f"[Layer3] 失败: {e}")

    # ---- Google Trends ----
    try:
        results["google_trends"]["trending"] = fetch_layer1_google_trends(geo=geo)
    except Exception as e:
        print(f"[Google Trends Trending] 失败: {e}")
        results["google_trends"]["trending"] = []

    try:
        results["google_trends"]["rising"] = fetch_layer2_google_trends(gt_terms, geo=geo)
    except Exception as e:
        print(f"[Google Trends Rising] 失败: {e}")
        results["google_trends"]["rising"] = []

    # ---- Reddit (降级) ----
    results["reddit"] = fetch_reddit_data_degraded(kw_dims)

    # ---- 动态关键词提取 (v5.2) ----
    try:
        existing_kw = set()
        for dim_words in kw_dims.values():
            existing_kw.update(dim_words)
        if dynamic_kw:
            existing_kw.update(dynamic_kw)
        results["new_keywords"] = extract_new_keywords(results["layer2"], existing_kw)
    except Exception as e:
        print(f"[Dynamic Keywords] 提取失败: {e}")
        results["new_keywords"] = []

    return results


if __name__ == "__main__":
    print("品牌社媒内容引擎 - 热门内容抓取脚本 v5.2")
    print(f"APIFY Token 配置状态: {'已配置' if APIFY_TOKEN else '未配置'}")
    print("三层架构: Layer1(平台trending) + Layer2(赛道搜索,排除品牌) + Layer3(品牌监测)")
    print("多维关键词矩阵: D1(产品) + D2(成分) + D3(症状) + D4(场景)")
