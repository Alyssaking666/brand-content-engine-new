# Brand Content Engine 🎯

> 品牌社媒内容全链路引擎 — 监测 → 选题 → 制作，一条龙

Coze Agent Skill，专为品牌社媒内容从业者打造。从热门内容监测到选题规划到内容制作，覆盖社媒运营全流程。

## 🧩 三大模块

### 模块1：trend-radar（热门内容监测）
- 每日抓取 **7个平台** 热门内容：X/Twitter · Instagram · TikTok · YouTube · Facebook · Reddit · Google Trends
- 支持 Apify 真实爬虫抓取（精确互动数据）或搜索降级模式
- **时间范围控制**：确保"今日热点"数据确实来自当天/48h内
- Google Trends Rising Keywords + Trending Searches
- 评分筛选框架（传播力/时效性/品牌相关性/可借鉴性）
- 每日报告 + 周五汇总

### 模块2：content-planner（每周选题规划）
- 基于监测数据 + 品牌 Content Pillar 自动生成下周5天选题
- 选题评分框架（热度/品牌相关性/Pillar重叠/可执行性）
- 每个选题明确：目标平台、展示形式、对应Pillar、文案方向

### 模块3：content-creator（品牌内容制作）
- **brand-voice-trainer**：品牌调性训练（语气/文案/视觉/视频/禁区）
- **copy-writer**：7种文案框架 + 品牌调性规则 + 平台长度约束
- **graphic-maker**：图文制作（信息图/轮播图/单图/产品图）
- **video-scripter**：视频脚本 + 爆款拆解模式
- **post-formatter**：6平台格式适配 + 发布前终检

## 📁 文件结构

```
brand-content-engine/
├── SKILL.md                          # 主文件：路由规则 + 全模块执行流程
├── scripts/
│   └── fetch_trends.py               # Apify 爬虫脚本（7平台 + 时间过滤）
└── references/
    ├── brand-voice-template.md       # 品牌调性档案模板
    ├── listening-config-template.md  # 监测配置模板（7平台 + Google Trends）
    ├── trend-report-template.md      # 每日热点报告模板
    ├── trend-summary-template.md     # 周汇总报告模板
    ├── content-plan-template.md      # 选题计划模板
    ├── copy-frameworks.md            # 7种文案框架参考
    └── platform-specs.md             # 各平台尺寸/排版规范
```

## ⚙️ 配置

### Apify Token（可选，推荐）

配置后 trend-radar 从搜索模式升级为真实爬虫抓取：

1. 注册 [Apify](https://apify.com/) 账号（免费计划含每月 $5 额度）
2. 进入 Console → Settings → Integrations 复制 API Token
3. 在 Coze Skill 凭证配置中添加 `APIFY_API_TOKEN`

| 未配置 | 已配置 |
|--------|--------|
| 搜索模式获取热门内容 | Apify 爬虫精确抓取 |
| 数据精度有限 | 精确互动量/播放量/发布时间 |
| Google Trends 降级为推断 | 真实 Rising Keywords + 热度曲线 |

### Apify Actor 清单

| 平台 | Actor ID | 定价 |
|------|----------|------|
| X/Twitter | `apidojo/twitter-scraper` | PPR |
| Instagram | `apify/instagram-api-scraper` | from $1.40/1k |
| TikTok | `thescrapelab/tiktok-scraper-2-0` | from $2/1k |
| YouTube | `streamers/youtube-scraper` | $2.40/1k |
| Facebook | `apify/facebook-pages-scraper` | PPR |
| Reddit | `betterdevsscrape/reddit-scraper` | $3/1k |
| Google Trends | `sourabhbgp/google-trends-scraper` | $2/1k |

## 🎯 触发词

| 触发词 | 模块 |
|--------|------|
| "今日热点" / "trending" | trend-radar |
| "本周汇总" | trend-radar（周汇总） |
| "下周选题" / "content plan" | content-planner |
| "训练品牌调性" / "brand voice" | brand-voice-trainer |
| "写文案" / "write copy" | copy-writer |
| "做图" / "carousel" | graphic-maker |
| "写脚本" / "video script" | video-scripter |
| "排版" / "format post" | post-formatter |

## 📄 License

MIT
