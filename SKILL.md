---
AIGC:
Label: "1"
ContentProducer: 001191110102MACQD9K64018705
ProduceID: 2556785148560384_0-data_volume/7646804706622472488-files/所有对话/主对话/PenPen/skill-files-v5.2/SKILL.md
ReservedCode1: ""
ContentPropagator: 001191110102MACQD9K64028705
PropagateID: 2556785148560384#1780547859194
ReservedCode2: ""
name: brand-content-engine
description: >
品牌社媒内容全链路引擎，涵盖三大模块：1）热门内容监测（trend-radar）：每日抓取 X/IG/TikTok/YouTube/Facebook/Reddit 各平台热门话题、爆款视频、Trending Music，每周五汇总；2）品牌社媒选题规划（content-planner）：基于监测数据+品牌Content Pillar，每周五出下周选题方向和内容计划；3）品牌内容制作（content-creator）：含品牌调性训练、文案撰写、图文制作、视频脚本、格式适配，从brand tone到成品一条龙。触发词："今日热点"、"每日热门"、"下周选题"、"内容计划"、"写文案"、"做图"、"写脚本"、"品牌调性"、"训练品牌voice"、"社媒内容"、"trending"、"content plan"
---
品牌社媒内容引擎 v5.2
三大模块一条龙：监测 → 选题 → 制作。每次触发时，根据用户意图自动路由到对应模块。
路由规则
用户意图	路由模块
"今日热点" / "daily trends" / "热门内容" / "trending"	模块1: trend-radar
"本周汇总" / "weekly summary"	模块1: trend-radar（周汇总模式）
"下周选题" / "content plan" / "选题方向"	模块2: content-planner
"训练品牌调性" / "build brand voice" / "学习品牌风格"	模块3: brand-voice-trainer
"写文案" / "write copy" / "draft post"	模块3: copy-writer
"做图" / "design graphic" / "carousel" / "infographic"	模块3: graphic-maker
"写脚本" / "video script" / "reels script" / "短视频"	模块3: video-scripter
"排版" / "format post" / "发布就绪"	模块3: post-formatter
共享依赖
所有模块读取：
`listening-config.md`（赛道/品牌/content pillars/监测配置/关键词矩阵/动态扩展关键词）
`brand-voice.md`（品牌定位与调性，由模块3.0训练生成；不存在时自动跳转brand-voice-trainer）
如 `listening-config.md` 不存在，首次运行时引导用户创建，使用 `references/listening-config-template.md` 模板。
如 `brand-voice.md` 不存在，自动跳转模块3.0（brand-voice-trainer）生成。
---
凭证说明
变量	用途	所需模块	获取方式
APIFY_API_TOKEN	各平台数据抓取（7平台）	trend-radar / brand-voice-trainer / video-scripter	Apify Console → Settings → Integrations → API token
GOOGLE_AI_API_KEY	Gemini 图片生成	graphic-maker	Google AI Studio
Apify Token 配置
注册 Apify 账号（免费计划含每月 $5 额度）
进入 Console → Integrations 复制 API Token
在 Coze Skill 凭证配置中添加 `APIFY_API_TOKEN`，值为复制的 Token
配置后能力提升：
trend-radar：从搜索模式升级为真实爬虫抓取，获取精确互动数据+原始链接
brand-voice-trainer：可直接抓取品牌社媒主页历史帖子
Google Trends：获取精确的搜索热度曲线和 Rising 关键词
无 Apify Token 时：trend-radar 降级为搜索模式（freshness 限定时间范围），数据精度降低但仍可用。Google Trends 部分降级为搜索推断。
模块1：trend-radar（每日热门监测）
三层架构（v4.0 核心变更）
> **trend-radar 从单层搜索升级为三层架构，解决"Top 5 是不是真的 Top 5"问题。**
每个平台产出三个板块，数据来源和爬虫规则完全不同：
层级	板块	数据来源	爬虫规则	是否为"真正的Top5"
Layer 1	🔥 平台热门 Top 5	平台原生trending/discover API	直接抓平台trending页面→过滤宠物/动物相关	✅ 是，来自平台自己的trending算法
Layer 2	🐾 赛道相关 Top 5	赛道关键词搜索	精确+泛化关键词→时间窗过滤→按互动排序→排除品牌自身	⚠️ 是"赛道内最高互动"，不是平台trending
Layer 3	📊 品牌动态	品牌主页抓取	直接抓品牌主页最新帖子	纯监测，不参与排名
关键规则：赛道相关板块排除品牌内容
🐾 赛道相关 Top 5 必须排除品牌自身账号发布的内容：
抓取结果中，如果 `author.username` / `ownerUsername` / `author.nickname` 匹配品牌账号（来自 listening-config.md 的品牌社媒主页链接），该条内容不得出现在赛道相关板块
品牌自身内容只出现在 📊 品牌动态 板块
品牌竞品的内容可以出现在赛道相关板块（竞品监测是有价值的）
监测平台 & Actor 配置
Layer 1: 平台热门（Platform Trending）
#	平台	Apify Actor ID	抓取目标	链接字段	筛选方式
1	X/Twitter	`automation-lab/twitter-trends-scraper`	美国Top50 trending topics + 搜索URL	`twitterSearchUrl`	从50条trending中过滤宠物/动物/dog相关
2	Instagram	`agentx/instagram-trending-scraper`	Explore feed trending + topic标签	`url` / `shortcode`	从Explore中过滤宠物/动物topic
3	TikTok	`coregent/tiktok-trend-discovery-scraper`	Trending hashtags + discovery数据	`url` / `webVideoUrl`	直接获取trending内容
4	YouTube	`streamers/youtube-scraper`	trending关键词搜索（YouTube无直接trending API）	`url`	搜索"trending"相关词，近似方案
5	Reddit	⚠️ 降级	Apify Reddit爬虫当前不可用	—	搜索补充：`site:reddit.com` + 热门话题
6	Facebook	❌ 无trending	Facebook 2018年移除公开trending功能	—	搜索补充或监测指定品牌主页
7	Google Trends	`sourabhbgp/google-trends-scraper`	Rising keywords + Trending searches	related articles links	直接输出rising数据
Layer 2: 赛道相关（Niche Relevant）
#	平台	Apify Actor ID	抓取目标	链接字段	品牌排除
1	X/Twitter	`kaitoeasyapi/twitter-x-data-tweet-scraper-pay-per-result-cheapest`	赛道关键词搜索推文	`url`	排除品牌账号
2	Instagram	`apify/instagram-hashtag-scraper`	Hashtag搜索帖子	`url`	排除品牌账号
3	TikTok	`thescrapelab/tiktok-scraper-2-0`	关键词视频搜索	`webVideoUrl` / `id`	排除品牌账号
4	YouTube	`streamers/youtube-scraper`	赛道关键词搜索视频	`url`	排除品牌频道
5	Reddit	⚠️ 降级	Apify Reddit爬虫当前不可用	—	搜索补充：`site:reddit.com` + 赛道关键词
6	Facebook	`apify/facebook-pages-scraper`	监测指定宠物品牌/群组主页	`url`	排除品牌主页
7	Google Trends	`sourabhbgp/google-trends-scraper`	赛道关键词explore模式	—	N/A
Layer 3: 品牌动态（Brand Monitor）
#	平台	Apify Actor ID	抓取目标	链接字段
1	Instagram	`apify/instagram-api-scraper` directUrls模式	品牌IG主页最新帖子	`url`
2	TikTok	`thescrapelab/tiktok-scraper-2-0` profile模式	品牌TikTok最新视频	`webVideoUrl`
3	YouTube	`streamers/youtube-scraper`	品牌YouTube频道	`url`
4	Facebook	`apify/facebook-pages-scraper`	品牌Facebook主页	`url`
> 注：品牌动态仅在用户明确要求或周五汇总时展示。日常每日报告默认只展示 Layer 1 + Layer 2。
各平台 Apify 输入参数
Layer 1: 平台热门
X/Twitter Trends (`automation-lab/twitter-trends-scraper`)：
```json
{
  "locations": ["United States", "Worldwide"],
  "maxItems": 100
}
```
输出字段：`name`(趋势名), `tweetVolume`(推文量), `twitterSearchUrl`(搜索URL), `locationName`, `isHashtag`
用途：获取Twitter真实trending topics，从中筛选宠物/动物相关
注意：返回的是trending topic名称和搜索链接，不是具体推文。需要再从搜索链接中找到具体推文
X/Twitter Trends 后续搜索 (`kaitoeasyapi/twitter-x-data-tweet-scraper-pay-per-result-cheapest`)：
```json
{
  "searchTerms": ["{trending topic from Layer 1}"],
  "maxTweets": 5,
  "sort": "Top"
}
```
用途：对Layer 1发现的宠物相关trending topic，搜索具体推文获取URL和互动数据
Instagram Explore (`agentx/instagram-trending-scraper`)：
```json
{
  "max_results": 50,
  "download_medias": "none",
  "country": "United States"
}
```
⚠️ country参数必填，必须使用全称"United States"（非"US"），否则Actor启动报错
输出字段：`id`, `caption`, `likesCount`, `url`, `section`(如"Fashion & Beauty"), `topic`(如"Street Fashion")
用途：获取IG Explore trending内容，从section/topic中筛选宠物/动物相关
TikTok Trend Discovery (`coregent/tiktok-trend-discovery-scraper`)：
```json
{}
```
输出字段：trending hashtags, trending videos, discovery data
用途：获取TikTok当前trending内容
YouTube (`streamers/youtube-scraper`)：
```json
{
  "searchQueries": ["trending pets today", "viral dog video", "trending animals"],
  "maxResults": 15
}
```
YouTube无直接trending API，用trending相关关键词搜索近似
Layer 2: 赛道相关（多维关键词矩阵驱动）
> Layer 2 的搜索词从 listening-config.md 的关键词矩阵(D1-D4) + 动态扩展关键词中组合生成，每个平台使用适配该平台的词组格式和维度优先级。
X/Twitter 赛道搜索 (`kaitoeasyapi/twitter-x-data-tweet-scraper-pay-per-result-cheapest`)：
```json
{
  "searchTerms": [
    "dog probiotic since:{date}", "dog supplement since:{date}",
    "dog allergy chews since:{date}", "my dog itchy skin since:{date}",
    "dog joint pain since:{date}", "dog upset stomach since:{date}",
    "dog gut health since:{date}", "senior dog mobility since:{date}"
  ],
  "maxTweets": 10,
  "sort": "Top"
}
```
优先维度：D3(症状) > D1(产品) > D4(场景)
无最低结果数限制
支持Twitter高级搜索语法：`since:`, `until:`, `lang:en`
输出字段：`url`, `text`, `likeCount`, `retweetCount`, `author.userName`, `createdAt`
排除品牌账号：结果中 `author.userName` 匹配品牌账号的条目丢弃
Instagram Hashtag (`apify/instagram-hashtag-scraper`)：
```json
{
  "hashtags": ["dogsupplement", "dogprobiotic", "doghealth", "dogwellness",
               "dogallergy", "dogjointhealth", "dognutrition", "healthydog",
               "petsupplements", "holisticpetcare"],
  "resultsLimit": 15
}
```
优先维度：D1(产品) > D4(场景) > D3(症状)
输出字段：`url`, `caption`, `likesCount`, `timestamp`, `ownerUsername`
排除品牌账号：结果中 `ownerUsername` 匹配品牌账号的条目丢弃
TikTok (`thescrapelab/tiktok-scraper-2-0`)：
```json
{
  "workflow": "keywords",
  "keywords": ["dog probiotic", "dog allergy relief", "itchy dog remedy", "#doghealth", "senior dog mobility"],
  "maxVideosPerKeyword": 5
}
```
优先维度：D3(症状) > D1(产品) > D4(场景)
限5个关键词（Actor不稳定，贪多超时）
输出字段：`webVideoUrl`, `text`, `statsV2.playCount`, `statsV2.diggCount`, `author.nickname`
排除品牌账号：结果中 `author.nickname` 匹配品牌账号的条目丢弃
YouTube (`streamers/youtube-scraper`)：
```json
{
  "searchQueries": ["best dog probiotic 2026", "dog supplement review",
                    "is glucosamine good for dogs", "dog allergy chews honest review",
                    "senior dog joint supplement", "dog probiotic before and after",
                    "vet recommended dog supplements", "dog itchy skin solution"],
  "maxResults": 10
}
```
优先维度：D1(产品) > D3(症状) > D2(成分) > D4(场景)
输出字段：`url`, `title`, `viewCount`, `numberOfLikes`, `channelName`
排除品牌频道：结果中 `channelName` 匹配品牌频道名的条目丢弃
Facebook (`apify/facebook-pages-scraper`)：
```json
{
  "startUrls": [{"url": "https://www.facebook.com/{competitor-brand-page}"}],
  "maxItems": 10
}
```
Facebook无trending功能，改为监测指定竞品/行业品牌主页
需要用户在 listening-config.md 中提供要监测的Facebook页面URL
Google Trends Explore (`sourabhbgp/google-trends-scraper`)：
```json
{
  "mode": "explore",
  "searchTerms": ["dog probiotic", "dog supplement", "pet supplements", "glucosamine for dogs", "dog joint supplement", "dog vitamins", "dog gut health"],
  "geo": "US",
  "time_range": "now 1-d"
}
```
优先维度：D1(产品) > D2(成分) > D3(症状)
输出：赛道关键词的搜索热度曲线 + Rising queries + Related topics
Layer 3: 品牌动态
Instagram 品牌主页 (`apify/instagram-api-scraper` directUrls模式)：
```json
{
  "directUrls": ["https://www.instagram.com/penpenpet/"],
  "resultsLimit": 10
}
```
TikTok 品牌主页 (`thescrapelab/tiktok-scraper-2-0` profile模式)：
```json
{
  "workflow": "profiles",
  "profiles": ["penpenpet"],
  "maxVideosPerProfile": 10
}
```
Reddit & Facebook 特殊处理
Reddit（Public JSON API 直连，v5.1）
方案：直接调用 Reddit Public JSON API，无需 Apify/OAuth，免费且无速率限制（浏览器级别请求）。
数据源：
热门帖：`https://www.reddit.com/r/{subreddit}/hot.json?limit=25`
月度Top帖：`https://www.reddit.com/r/{subreddit}/top.json?t=month&limit=25`
垂类 Subreddit 列表（从 listening-config.md 读取，默认12个）：
类别	Subreddit	说明
核心养狗	dogs, DogCare, puppy101	综合养狗讨论
狗健康	DogHealth, AskVet, DogAllergies	健康问题+兽医建议
狗粮/营养	dogfood, rawpetfood	饮食和营养补充
综合宠物	pets, PetHealth	泛宠物讨论
生活方式	seniordogs, reactivedogs	特定养宠场景
自然/整全	NaturalPetCare	天然保健讨论
筛选规则：
只抓取垂类相关subreddit，不抓r/all等泛版块
合并 hot + top(month) 后去重
关键词相关性过滤（v5.2新增）：标题或正文需包含 D1-D4 任一维度关键词（宽松匹配），或讨论与宠物健康/营养/保健品相关的话题
门槛：upvotes>50 且 评论数>20
按互动量排序，取Top 10
返回字段：
`title`（帖子标题）、`url` / `permalink`（原始链接）、`score`（upvotes）、`num_comments`（评论数）、`subreddit`、`created_utc`（发布时间）、`selftext`（正文摘要）
降级：
如环境无法访问 reddit.com（沙箱网络限制），降级为搜索补充：`site:reddit.com` + 赛道关键词 + `freshness=7`（近7天）
Facebook（无公开trending功能）
现状：Facebook 2018年移除了公开Trending功能。`apify/facebook-pages-scraper` 只能抓取指定主页，无法搜索或获取trending。
降级方案（默认）：
搜索补充Facebook数据
监测指定竞品/行业品牌Facebook主页（需用户在listening-config.md中提供URL）
时间范围控制（核心）
> **trend-radar 的核心价值在于时效性。所有抓取操作必须明确限定时间范围，确保"今日热点"产出的数据确实来自当天或近48h。**
时间范围规则
模式	数据时间范围	说明
每日热点（默认）	当天 00:00 ~ 当前时刻	核心抓取窗口，优先24h内
每日热点（扩展）	过去48h	如当日数据不足，自动扩展至48h
周汇总	过去7天（周一~周日）	汇总一周趋势演变
各平台时间过滤实现
平台	Layer 1时间处理	Layer 2时间处理
X/Twitter	Trends自带时效性（实时热门）	`since:YYYY-MM-DD until:YYYY-MM-DD` 语法
Instagram	Explore自带时效性	抓取后按 `timestamp` 字段过滤
TikTok	Trending自带时效性	抓取后按 `createTime` 字段过滤
YouTube	搜索后按发布时间过滤	搜索后按发布时间过滤
Reddit	N/A（降级为搜索）	搜索设置freshness
Facebook	N/A	抓取后按 `time` 过滤
Google Trends	内置 `time_range` 参数	内置 `time_range` 参数
数据准入规则（硬约束）
仅监测海外主流社媒平台：X/Twitter、Instagram、TikTok、YouTube、Facebook、Reddit + Google Trends。排除所有国内平台（天猫、淘宝、微博、小红书、抖音国内版、拼多多等），搜索结果中涉及国内平台的内容一律过滤掉。
链接必填：每条入选内容必须附带原始来源 URL，方便点击验证和追溯。无链接的内容不得录入报告。
时间窗验证：所有内容必须经过发布时间校验，超出时间窗口的丢弃。
赛道相关排除品牌自身：🐾赛道相关板块中，品牌账号发布的内容一律排除，只展示第三方内容。
Layer 1 宠物相关性过滤：🔥平台热门板块从平台trending中筛选时，必须包含宠物/动物/dog/宠物健康相关关键词才算入选。
数据质量门槛（v5.1更新）：
视频类内容（YouTube/TikTok/IG Reels）：曝光量≥100,000 且 likes>1,000
图片类内容（IG图片/Facebook帖文）：likes>1,000
推文（Twitter）：likes>500
Reddit帖子：upvotes>50 且 评论数>20（仅展示垂类subreddit当月top+hot帖文）
低于门槛的内容不展示，但可在报告末尾以"最接近门槛内容"形式标注（标记📊），供参考
赛道相关展示数量：每个平台Layer2展示Top 10（按曝光+互动排序），非Top 5
筛选评分框架
Layer 1: 平台热门评分
维度	权重	说明
平台排名	40%	在平台trending列表中的排名
宠物相关性	30%	与宠物/动物/狗话题的关联度
传播力	20%	互动量绝对值
品牌嫁接潜力	10%	是否可与品牌内容结合
Layer 2: 赛道相关评分（≥7分入选）
维度	权重	说明
传播力	35%	互动量/播放量绝对值 + 增速
时效性	20%	24-48h内爆发优先，超出窗口降权
品牌相关性	25%	与 listening-config.md 关键词矩阵匹配的维度数（命中≥2个维度加分）
可借鉴性	20%	内容形式/钩子/叙事是否可迁移到品牌内容
多维度覆盖检查：Layer 2 最终 Top 10 结果应覆盖至少 2 个关键词维度（如只命中 D1 产品层，需检查其他维度是否有数据未被捕获），避免同质化。
多维关键词矩阵系统（v5.2 核心升级）
> **从线性泛化（产品→品类→生活方式→情感）升级为4维关键词矩阵，每个平台使用不同的搜索词组合和格式，大幅提升赛道内容捕获覆盖面。**
关键词维度定义
所有维度的具体词汇由 `listening-config.md` 的 `## 关键词矩阵` 板块定义，以下为框架：
维度	说明	适用平台	示例（宠物保健品赛道）
D1: 产品层(Product)	品类通用名+产品形态	全平台	dog probiotic, dog supplement, joint chews, allergy chews, calming treats, dental chews, hip and joint, multivitamin dogs
D2: 成分层(Ingredient)	核心功效成分	YouTube + Google Trends	glucosamine dogs, fish oil dogs, turmeric pet, omega 3 dogs, prebiotic dogs, collagen dogs, digestive enzymes dogs
D3: 症状/痛点层(Symptom)	宠主搜索的问题描述	全平台（Twitter/Reddit优先）	dog itchy skin, dog diarrhea, dog joint pain, senior dog mobility, dog upset stomach, dog hair loss, dog bad breath, dog anxiety, dog hot spots
D4: 场景层(Scenario)	养宠生活场景	YouTube + IG + TikTok	dog wellness routine, aging dog care, rescue dog nutrition, new puppy essentials, senior dog quality of life, dog preventive health
> **维度选用策略**：D1和D3是全平台必用维度；D2(成分)仅在YouTube和Google Trends使用（其他平台搜索量太低）；D4(场景)仅在YouTube/IG/TikTok使用。
平台搜索词适配规则
> 同一个品类在不同平台的"语言"完全不同，搜索词必须适配平台原生表达。
平台	搜索特性	优先维度	搜索词格式要求	每次搜索词数量
TikTok	Hashtag+短口语驱动，算法推荐为主	D3 > D1 > D4	无空格hashtag + 口语短句	5个（Actor不稳定，贪多超时）
Instagram	Hashtag精确匹配，Explore推荐	D1 > D4 > D3	无空格合成hashtag	8-10个
YouTube	长尾搜索，review/教程导向	D1 > D3 > D2 > D4	问句/review句式/年份词	8-10个
X/Twitter	短语+自然语言，实时讨论	D3 > D1 > D4	自然语言短句，支持高级搜索语法	8-10个
Reddit	问题导向，求助/推荐/讨论	D3 > D1 > D4	通过subreddit + 关键词相关性过滤	N/A（subreddit驱动）
Google Trends	搜索量词根，精确匹配	D1 > D2 > D3	简短品类词根	5-8个
各平台搜索词示例（基于宠物保健品赛道）
TikTok 搜索词组（5个，精选最高价值词）：
```json
{
  "keywords": ["dog probiotic", "dog allergy relief", "itchy dog remedy", "#doghealth", "senior dog mobility"]
}
```
Instagram 搜索词组（8-10个hashtag）：
```json
{
  "hashtags": ["dogsupplement", "dogprobiotic", "doghealth", "dogwellness", "dogallergy", "dogjointhealth", "dognutrition", "healthydog", "petsupplements", "holisticpetcare"]
}
```
YouTube 搜索词组（8-10个）：
```json
{
  "searchQueries": ["best dog probiotic 2026", "dog supplement review", "is glucosamine good for dogs", "dog allergy chews honest review", "senior dog joint supplement", "dog probiotic before and after", "vet recommended dog supplements", "dog itchy skin solution"]
}
```
X/Twitter 搜索词组（8-10个）：
```json
{
  "searchTerms": ["dog probiotic since:{date}", "dog supplement since:{date}", "dog allergy chews since:{date}", "my dog itchy skin since:{date}", "dog joint pain since:{date}", "dog upset stomach since:{date}", "dog gut health since:{date}", "senior dog mobility since:{date}"]
}
```
Google Trends 搜索词组（5-8个）：
```json
{
  "searchTerms": ["dog probiotic", "dog supplement", "pet supplements", "glucosamine for dogs", "dog joint supplement", "dog vitamins", "dog gut health"]
}
```
动态关键词反馈环（v5.2 新增）
> 解决"今天发现的热词不会补充进明天搜索"的问题。每日自动学习，越用越精准。
机制：
Day N 执行完成 → 从 Layer 2 Top 10 结果中提取：
高频出现的新 hashtag（出现≥3次且不在现有词库中）
新发现的竞品品牌名
→ 写入 `listening-config.md` 的 `## 动态扩展关键词` 板块（追加模式，带日期标签）
→ Day N+1 执行时自动读取，纳入搜索词组
listening-config.md 动态扩展关键词格式：
```markdown
## 动态扩展关键词
> 自动提取，有效期14天，最多保留30个，过期移入归档区

### 2026-06-04 新发现
- [TikTok] #dogbiome (出现5次, 来自Top10中3条内容)
- [Instagram] #rawfeddogs (出现4次)
- [YouTube] "dog microbiome supplement" (Top1标题关键词)
- [竞品] "BarkBiotics" (新品牌, 出现在3个平台)

### 2026-06-03 新发现
- [TikTok] #allergydogmom (出现3次)
- [X/Twitter] "dog skin barrier" (高互动推文关键词)
```
反馈环规则：
每次执行后自动提取，无需人工干预
扩展词有效期 14 天，超过 14 天未再出现则移入归档区
扩展词最多保留 30 个（超出时按最近出现时间淘汰最旧的）
用户可手动编辑 `listening-config.md` 的动态扩展板块添加/删除词
每日执行流程
读取 `listening-config.md`，确认监测平台、子版块、阈值、关键词矩阵(D1-D4)、动态扩展关键词、品牌账号列表
组装搜索词：按平台适配规则，从关键词矩阵各维度 + 动态扩展关键词中组合生成每个平台的搜索词组（TikTok限5个，其他平台8-10个）
计算时间范围：确定 start_date = 当天 00:00，end_date = 当前时刻；如当日数据不足扩展至48h
Layer 1 抓取：平台热门（如配置了 `APIFY_API_TOKEN`）：
Twitter: `automation-lab/twitter-trends-scraper` → 获取美国Top50 trending → 筛选宠物/动物相关
Instagram: `agentx/instagram-trending-scraper` → 获取Explore trending → 筛选宠物/动物topic
TikTok: `coregent/tiktok-trend-discovery-scraper` → 获取trending内容
YouTube: `streamers/youtube-scraper` → trending关键词搜索
Google Trends: `sourabhbgp/google-trends-scraper` → trending模式
Reddit/Facebook: 搜索补充（`site:reddit.com trending pets` 等）
提取链接：从Apify返回数据中提取链接字段，每条结果必须有可点击链接
Layer 2 抓取：赛道相关（如配置了 `APIFY_API_TOKEN`）：
Twitter: `kaitoeasyapi/twitter-x-data-tweet-scraper-pay-per-result-cheapest` → 多维关键词搜索（8-10词，D3>D1>D4）
Instagram: `apify/instagram-hashtag-scraper` → 多维Hashtag搜索（8-10个，D1>D4>D3）
TikTok: `thescrapelab/tiktok-scraper-2-0` → 多维关键词搜索（5词，D3>D1>D4）
YouTube: `streamers/youtube-scraper` → 多维关键词搜索（8-10词，D1>D3>D2>D4）
Facebook: `apify/facebook-pages-scraper` → 监测指定竞品主页
Google Trends: `sourabhbgp/google-trends-scraper` → explore模式（5-8词，D1>D2>D3）
Reddit: Public JSON API → 扩展垂类subreddit(12个)的hot+top(month)帖文 + 关键词相关性过滤
提取链接：从Apify返回数据中提取链接字段
排除品牌内容：过滤掉品牌账号发布的内容
Reddit 垂类抓取（独立步骤）：
读取 listening-config.md 的 subreddits 配置（12个垂类社区）
对每个subreddit调用 `hot.json` + `top.json?t=month`
合并去重，关键词相关性过滤（标题/正文包含D1-D4维度关键词）
过滤：upvotes>50 且 评论>20
按互动量排序取Top 10
如环境无法访问 reddit.com，降级为搜索补充
数据质量门槛过滤（v5.1）：
视频类（YouTube/TikTok/IG Reels）：曝光≥100K 且 likes>1,000
图片类（IG图片/Facebook）：likes>1,000
推文（Twitter）：likes>500
Reddit：upvotes>50 且 评论>20
低于门槛的内容不展示，在报告末尾标注📊
Layer 3 抓取：品牌动态（仅周五汇总或用户明确要求时）：
抓取品牌各社媒主页最新帖子
产出独立板块，不与Layer 1/2混合
验证时间：检查所有抓取结果的发布时间，丢弃超出时间窗口的内容
筛选评分：
Layer 1 平台热门：按平台排名+宠物相关性打分，Top 5
Layer 2 赛道相关：按评分框架打分，Top 10（排除品牌内容），再按数据质量门槛过滤
多维度覆盖检查：确认Top 10覆盖≥2个关键词维度
Google Trends Rising Keywords：单独输出赛道相关的 Rising 查询词和热度变化
热度×赛道交叉洞察：分析Layer 1平台热门与Layer 2赛道内容的结合点（形式/话题/情绪/BGM）
动态关键词提取（v5.2新增）：
从本次 Layer 2 Top 10 结果中提取新 hashtag（出现≥3次且不在现有词库）和竞品品牌名
写入 listening-config.md 的 `## 动态扩展关键词` 板块（带日期标签）
清理超过14天的过期词
读取 `references/trend-report-template.md`，填充产出报告（含数据时间窗元信息+爬虫规则说明）
保存为 `trend-reports/{date}-daily.md`
降级模式（无 Apify Token）
Layer 1 + Layer 2 均降级为搜索模式：
必须使用 `freshness` 参数限定时间范围
必须附加排除关键词：`-天猫 -淘宝 -微博 -小红书 -拼多多`
搜索词组扩展：即使降级模式也使用多维关键词矩阵，每个平台按维度优先级组合搜索词
保留原始链接：每条搜索结果必须提取并保留原始 URL
Layer 2 搜索关键词中排除品牌账号名
报告结构顺序（v5.1 — 结果先行，数据来源后置）
报告输出按以下顺序排列，洞察和结果先行，技术细节放最后：
💡 今日一句话洞察 — 最值得关注的趋势+品牌启示
🎯 热度×赛道交叉洞察 — Layer 1热门与Layer 2赛道的结合点
🔥 跨平台共振话题 TOP 5
📈 Google Trends — Rising Keywords
📱 各平台热门内容 — 每个平台🔥平台热门Top5 + 🐾赛道相关Top10，不标注数据来源（统一放最后）
💬 Reddit 垂类社区热帖 — 垂类subreddit当月top+hot帖文（upvotes>50，评论>20）
🎵 本日热门音乐/BGM
🔑 新发现关键词 — 本次执行发现的新关键词/hashtag（已写入动态扩展词库）
📊 低于门槛参考内容 — 接近但未达门槛的内容，标注📊供参考
🔍 数据来源与质量说明 — 统一放在最后，含：三层架构说明、各平台数据来源表、数据质量门槛、已知局限性
爬虫规则说明（v5.1 — 统一放报告末尾）
每个平台的爬虫规则和数据来源不在平台板块内标注，统一放在报告末尾的「🔍 数据来源与质量说明」板块。
周五汇总模式
在每日报告基础上额外产出：
跨平台共振 TOP 5
趋势演变（持续/昙花/上升）
本周热门 BGM TOP 5
Reddit 用户深度关注点（本周高互动帖文话题聚类）
与品牌 Content Pillar 的关联建议
📊品牌动态汇总（本周品牌各平台表现）
🔑 本周关键词矩阵表现回顾（哪些维度产出多/哪些维度需补充）
📋 关键词矩阵优化建议（建议新增/淘汰的词）
读取 `references/trend-summary-template.md`，保存为 `trend-reports/week-{nn}-summary.md`
---
模块2：content-planner（每周选题规划）
触发时机
每周五，或用户主动请求下周选题。
依赖
模块1的 `trend-reports/` 或 `week-{nn}-summary.md`（本周热点数据）
`listening-config.md` 中的 Content Pillars 和当月主推
`brand-voice.md`（品牌定位与调性，由模块3.0训练生成；如不存在自动跳转brand-voice-trainer）
选题评分框架
维度	权重	说明
热度	30%	本周该话题在各平台的传播力
品牌&产品相关性	35%	与品牌定位/当月主推产品的关联
Content Pillar 重叠	25%	必须命中至少1个 pillar
可执行性	10%	制作难度、素材可获得性
防重复机制
同一热点在多天出现时，通过5个变量排列组合确保内容不重复：
切入角度（痛点识别/情感驱动/科学背书/UGC验证/生活场景/趣味共鸣）— 保证内容角度不同
钩子类型（提问式/情感式/数据式/惊喜式/活动式）— 保证开头不重复
内容形式（Carousel/Reel/单图/Thread/Short/Meme梗图）— 保证视觉不重复
平台（TikTok/IG/FB/YouTube）— 保证受众不重叠
Pillar（5个轮转）— 保证品牌调性覆盖
硬规则：同一周内，不允许出现"切入角度+钩子类型"完全相同的两篇选题。同一热点连续两天出现时，必须切换角度和钩子。
平台分发规则
视频类（Reel/Short）：TikTok + Instagram + Facebook + YouTube 多平台分发
图文类（Carousel/单图）：Instagram + Facebook 分发
聚焦平台：TikTok、Instagram、Facebook、YouTube
执行流程
读取本周 trend-summary（或最新trend-report）
读取 listening-config.md 的 Content Pillars 和当月主推
读取 brand-voice.md，确保所有文案遵循品牌调性（语气参数、钩子偏好、CTA偏好、禁区）
按评分框架对每个热点话题评分
为下周一~周五安排每日选题，覆盖不同 pillar，应用防重复机制
每个选题明确：日期、平台、选题方向、内容形式、主推产品、制作难度、Content Pillar归属、热度来源
提供完整文案内容：帖文文案（Carousel逐页/视频逐段结构）+ 发布文案 + 使用hashtag
检查 pillar 覆盖均衡性和防重复规则
备选选题以表格形式罗列（选题方向/平台/形式/产品/难度/热度来源）
读取 `references/content-plan-template.md`，保存为 `content-plans/week-{nn}-plan.md`
输出结构
🎯 本周内容主轴 + 当月主推产品关联
📅 当周内容规划（每天一份，含完整文案）
📋 备选选题（表格）
📊 Content Pillar覆盖检查 + 产品露出分布
🔮 下周值得关注
梗图（Meme）选题指引
Pillar #5「品牌情感与文化」支持梗图选题，规则如下：
核心原则：只有养宠人才懂的共鸣，不是硬塞产品的广告
切入角度：趣味共鸣（养宠日常的荒诞/心酸/可爱瞬间）
内容形式：Meme梗图（单图/Carousel均可）
分发平台：IG + FB（图文）为主，TikTok可做短视频meme
制作难度：低（无需拍摄，可用素材+文字排版）
品牌露出：自然融入即可——角落Logo、品牌色边框、PenPen标志性用语（paw-some / Fur Sure等），不强加产品
选题来源：trending meme格式 × 养宠场景改编（如"when your dog…"、"POV: you're a dog parent…"）
频率建议：每周1-2条梗图，穿插在Pillar 1-4的硬核内容之间，调节节奏
禁区：不用悲伤/负面狗狗画面、不调侃疾病痛苦、不涉及争议话题
---
模块3：content-creator（品牌内容制作）
3.0 brand-voice-trainer（品牌调性训练）
> 所有内容制作子技能的前置依赖。brand-voice.md 不存在时自动跳转此技能。
执行流程
向用户索取品牌过往社媒内容（最少10条，建议20条，覆盖不同平台和内容类型）
收集方式三选一：A.用户粘贴文本 B.Apify抓取品牌主页 C.上传CSV
多维度分析样本：
语气与性格（3-5关键词 + 温度/正式度/自信度 1-10）
文案特征（平均句长/段落节奏/钩子类型/CTA风格/标志用语）
视觉风格（主色/排版/字体/调性）
视频风格（时长偏好/节奏/出镜方式/BGM偏好）
禁区识别（absence signals：从未出现的用词/结构/语气）
平台差异化（同品牌在不同平台的语气差异）
产出 `brand-voice.md`，读取 `references/brand-voice-template.md` 模板
回测验证：用规则重写3条样本，匹配度≥80%则通过
核心产出
`brand-voice.md`，包含：品牌性格、语气参数、文案规则(要做/不做)、钩子偏好、CTA偏好、标志用语、平台差异化表、视觉规范、视频规范、品牌禁区。
3.1 copy-writer（文案撰写）
前置检查
读取 brand-voice.md，不存在→跳转 brand-voice-trainer
读取本周 content-plan（如有）
读取 listening-config.md（content pillars）
执行流程
确定选题&平台：从 content-plan 提取 / 用户指定 / 用户粘贴素材
选择框架（按内容类型匹配）：
内容类型	框架	结构
痛点切入	PAS	Pain→Agitate→Solve
产品推广	AIDA	Attention→Interest→Desire→Action
场景对比	BAB	Before→After→Bridge
用户故事	STAR	Situation→Task→Action→Result
观点输出	SLAY	Statement→List→Application→You
教程干货	How-to	问题→步骤→总结
种草安利	PDR	Problem→Demo→Result
撰写草稿，严格执行 brand-voice.md 规则：
语气/正式度/自信度 → 对应用词句式
钩子 → 使用偏好排序前3的类型
CTA → 使用指定风格
禁区 → 逐条检查，违反则重写
平台差异化 → 按目标平台调整
各平台长度硬约束：
平台	推荐长度	Hashtag数	首行规则
IG	≤150词	5-7	不看more也能读
TikTok	≤80词	3-5	前2s决定留存
X	≤280字符	1-2	全文可见
LinkedIn	≤1,300字符	3-5	钩子+空行
YouTube	≤200词描述	标签区	标题即钩子
Facebook	≤250词	3-5	钩子
自检：品牌调性匹配/钩子强度/CTA明确/长度合规/禁区触碰
保存为 `drafts/{date}-{topic}-{platform}.md`
3.2 graphic-maker（图文制作）
前置检查
读取 brand-voice.md（视觉规范部分）
如有 brand-kit.md，优先读取
读取关联文案草稿
内容类型判断
内容特征	推荐类型	适配平台
数据/对比/流程/框架	信息图 Infographic	IG Carousel / LinkedIn
观点/清单/步骤/教程	轮播图 Carousel	IG / LinkedIn / Facebook
金句/预告/公告/种草	单图 Single Post	IG / X / Facebook
产品展示/新功能	产品图 Product Shot	全平台
平台尺寸硬约束
读取 `references/platform-specs.md` 获取完整尺寸表。核心规格：
类型	平台	尺寸(px)	比例
方形帖	IG/LinkedIn/FB	1080×1080	1:1
竖版帖	IG	1080×1350	4:5
Stories/Reels封面	IG/FB	1080×1920	9:16
横版帖	X/LinkedIn	1200×675	16:9
Carousel	IG/LinkedIn	1080×1350	4:5
YouTube缩略图	YouTube	1280×720	16:9
TikTok封面	TikTok	1080×1920	9:16
生成方式（三选一）
方式A：image_generate 直出（推荐）
构建 prompt：[平台标识] + 品牌视觉关键词 + 内容类型 + 尺寸 + 品牌色 + 文字内容(双引号) + 排版要求。调用 image_generate 工具直接生成图片。
方式B：Gemini Prompt 输出
适用白板手绘风/复杂信息图。输出完整 Gemini image generation prompt，用户复制到 Gemini chat 的 Create Image 模式。
方式C：Canva 设计规范
适用需人工微调。输出 Canva 可导入的设计指令文档（元素清单+文字内容+导出设置）。
Carousel 多页规范
逐页生成，风格参数一致
封面页 + 内容页 + CTA 页，视觉区分
每页 body 文字 ≤15 词
保存到 `assets/{date}-{topic}-{platform}/`
3.3 video-scripter（视频脚本+制作）
前置检查
读取 brand-voice.md（文案规则 + 视频规范）
读取关联文案草稿 / content-plan 选题
如有参考爆款链接，进入「爆款拆解」模式
视频类型
类型	时长	适配平台
短Reel	≤15s	TikTok/IG Reel
标准Reel	30s	TikTok/IG Reel/YouTube Shorts
深Reel	60s	TikTok/IG Reel/YouTube Shorts
长视频	3-10min	YouTube
爆款拆解模式
抓取参考视频数据
分析结构：钩子→冲突→高潮→CTA
提取可借鉴元素（钩子类型/节奏/BGM/画面切换）
按 brand-voice.md 重写：保留结构骨架，替换品牌语气
脚本模板
分镜表：时间 | 画面 | 旁白/字幕 | 音乐/BGM | 备注
全局规则
前2s必须有强钩子
旁白语气匹配 brand-voice.md
每5-7s一个节奏变化点
CTA在最后3s
竖版：1080×1920, 9:16 | 横版：1920×1080, 16:9
生成方式
方式A：create_project(sub_type=2) AI视频生成
方式B：graphic-maker生成分镜图 + 拍摄指南
方式C：纯脚本文档交付
3.4 post-formatter（格式适配 & 发布就绪）
前置检查
读取 brand-voice.md
读取待发布文案草稿
读取关联图片/视频素材
各平台排版规范
读取 `references/platform-specs.md` 获取完整规则。核心要点：
IG：钩子不看more可读，空行分段，Hashtag末尾5-7个用"."分隔
TikTok：精简≤80词，字幕必须内嵌，Hashtag 3-5个
X：280字符硬上限，Hashtag 1-2个
LinkedIn：空行分隔每段，钩子加粗≤50字符，Hashtag 3-5个
YouTube：标题≤70字符含关键词，描述前150词放核心信息，时间戳(≥3min)
Facebook：≤250词推荐，Hashtag 3-5个
发布前终检清单
品牌调性：语气一致/无禁区内容/CTA符合规范
内容质量：钩子有效/CTA明确/无错别字敏感词
平台合规：长度/Hashtag数/图片尺寸/视频格式
内容一致性：与content-plan一致/命中Content Pillar/多平台核心信息一致/图文匹配
素材检查：图片视频已生成/格式正确/大小合规
产出
为每个平台产出 `publish-ready/{date}-{topic}-{platform}.md`，含：排版后文案(可直接复制)、素材路径、终检结果、建议发布时间。
---
变更日志
v4.0 (2026-06-03)
三层架构：从单层搜索升级为 Layer1(平台trending) + Layer2(赛道搜索) + Layer3(品牌监测)
Twitter Actor替换：apidojo/tweet-scraper(50条最低限制) → kaitoeasyapi/twitter-x-data-tweet-scraper-pay-per-result-cheapest(无限制)
新增平台trending Actor：automation-lab/twitter-trends-scraper(Twitter trending), agentx/instagram-trending-scraper(IG Explore), coregent/tiktok-trend-discovery-scraper(TikTok trending)
Instagram赛道修复：从directUrls(品牌主页)改为instagram-hashtag-scraper(hashtag搜索)，赛道相关板块排除品牌自身内容
Reddit降级说明：明确标注Apify Reddit爬虫当前不可用，默认搜索补充，可选OAuth模式升级
Facebook降级说明：明确标注Facebook无公开trending功能，改为指定主页监测+搜索补充
爬虫规则透明标注：每个平台标注数据来源、爬虫规则、局限性
品牌内容排除规则：赛道相关板块必须排除品牌账号内容
v5.0 (2026-06-03)
数据质量门槛：曝光≥500K+互动率≥5%（视频）/ likes≥10K（图片）/ likes≥500（推文）/ upvotes≥500（Reddit）
赛道相关展示Top 10：每个平台Layer2展示Top 10（非Top 5）
Reddit Public JSON API方案：替代Apify爬虫，直接调用reddit.com/.json端点
报告结构重组：结果先行，数据来源统一放末尾，移除平台板块内爬虫规则标注
Instagram Trending country修复：必须用全称"United States"而非"US"
v5.1 (2026-06-03)
门槛下调更贴合赛道现实：
视频：曝光≥100K + likes>1,000（原500K+5%互动率）
图片/Facebook：likes>1,000（原10K）
Twitter：likes>500（不变）
Reddit：upvotes>50 + 评论>20（原500 upvotes）
Reddit改为垂类社区抓取：只看垂类subreddit（dogs/DogCare/DogHealth等）的当月top+hot帖文，不再抓r/all泛版块
Reddit数据源：hot.json + top.json?t=month 双端点合并去重
报告新增板块：Reddit垂类社区热帖独立板块 + 低于门槛参考内容板块
v5.2 (2026-06-04)
多维关键词矩阵系统：从线性泛化(产品→品类→生活方式→情感)升级为4维关键词矩阵(D1产品+D2成分+D3症状+D4场景)，每个平台按不同维度优先级和格式组合搜索词
维度选用策略：D1+D3全平台必用；D2(成分)仅YouTube+Google Trends；D4(场景)仅YouTube/IG/TikTok
平台搜索词适配规则：TikTok限5词(Actor不稳定)、IG用hashtag格式8-10个、YouTube用问句/review句式8-10个、Twitter用自然语言+高级搜索语法8-10个、Google Trends用词根5-8个
动态关键词反馈环：每次执行后从L2 Top10提取新hashtag(≥3次)和竞品品牌名，写入listening-config.md动态扩展板块，14天有效期，最多30个
Reddit垂类社区扩展：从7个subreddit扩展到12个(新增puppy101/DogAllergies/rawpetfood/seniordogs/reactivedogs/NaturalPetCare)
Reddit关键词相关性过滤：帖子标题或正文需包含D1-D4维度关键词，过滤不相关内容
L2评分框架调整：品牌相关性权重25%(原20%)，按关键词矩阵命中维度数评分；新增多维度覆盖检查(Top10需覆盖≥2个维度)
报告新增板块：🔑新发现关键词(第8位)，展示本次执行学到的动态词
周五汇总新增：本周关键词矩阵表现回顾 + 优化建议
Layer2 Actor输入参数更新：所有平台搜索词改为多维矩阵驱动，标注维度优先级
---
> 本内容由 Coze AI 生成，请遵循相关法律法规及《人工智能生成合成内容标识办法》使用与传播。
