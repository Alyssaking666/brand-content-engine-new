---
name: brand-content-engine
description: >
  品牌社媒内容全链路引擎，涵盖三大模块：1）热门内容监测（trend-radar）：每日抓取 X/IG/TikTok/YouTube/Facebook/Reddit 各平台热门话题、爆款视频、Trending Music，每周五汇总；2）品牌社媒选题规划（content-planner）：基于监测数据+品牌Content Pillar，每周五出下周选题方向和内容计划；3）品牌内容制作（content-creator）：含品牌调性训练、文案撰写、图文制作、视频脚本、格式适配，从brand tone到成品一条龙。触发词："今日热点"、"每日热门"、"下周选题"、"内容计划"、"写文案"、"做图"、"写脚本"、"品牌调性"、"训练品牌voice"、"社媒内容"、"trending"、"content plan"
---

# 品牌社媒内容引擎

三大模块一条龙：**监测 → 选题 → 制作**。每次触发时，根据用户意图自动路由到对应模块。

## 路由规则

| 用户意图 | 路由模块 |
|---------|---------|
| "今日热点" / "daily trends" / "热门内容" / "trending" | 模块1: trend-radar |
| "本周汇总" / "weekly summary" | 模块1: trend-radar（周汇总模式）|
| "下周选题" / "content plan" / "选题方向" | 模块2: content-planner |
| "训练品牌调性" / "build brand voice" / "学习品牌风格" | 模块3: brand-voice-trainer |
| "写文案" / "write copy" / "draft post" | 模块3: copy-writer |
| "做图" / "design graphic" / "carousel" / "infographic" | 模块3: graphic-maker |
| "写脚本" / "video script" / "reels script" / "短视频" | 模块3: video-scripter |
| "排版" / "format post" / "发布就绪" | 模块3: post-formatter |

## 共享依赖

所有模块读取：
- `listening-config.md`（赛道/品牌/content pillars/监测配置）
- `about-me.md` + `voice.md`（如已有，来自 voice-builder）

如 `listening-config.md` 不存在，首次运行时引导用户创建，使用 `references/listening-config-template.md` 模板。

---

# 模块1：trend-radar（每日热门监测）

## 监测平台 & 数据源

| 平台 | Apify Actor | 抓取内容 | 入选阈值 |
|------|------------|---------|---------|
| X/Twitter | apidojo/twitter-scraper | Trending topics + 高互动帖 | 互动>10k 或 24h转发>1k |
| Instagram | apidojo/instagram-scraper | 热门 Reels + 话题标签帖 | 播放>500k 或点赞>50k |
| TikTok | apidojo/tiktok-scraper | Trending videos + 热门音乐 | 播放>1M 或7d增长>300% |
| YouTube | apidojo/youtube-scraper | 热门视频 + Rising keywords | 播放>500k 或48h涨幅显著 |
| Facebook | apidojo/facebook-scraper | 热门帖文 + 群组讨论 | 互动>5k 或分享>500 |
| Reddit | apidojo/reddit-scraper | 垂直子版块热帖 + Rising | Upvotes>500 或评论>200 |

## 筛选评分框架

每条内容按以下维度打分（满分10），≥7分入选：

| 维度 | 权重 | 说明 |
|------|------|------|
| 传播力 | 40% | 互动量/播放量绝对值 + 增速 |
| 时效性 | 25% | 24-48h内爆发优先 |
| 品牌相关性 | 20% | 与 listening-config.md 中赛道/产品关键词匹配度 |
| 可借鉴性 | 15% | 内容形式/钩子/叙事是否可迁移到品牌内容 |

## 每日执行流程

1. 读取 `listening-config.md`，确认监测平台、子版块、阈值
2. 如配置了 `APIFY_API_TOKEN`，调用 `scripts/fetch_trends.py` 抓取数据
3. 如无 API Token，使用搜索工具获取各平台当日热门内容
4. 按评分框架筛选，每平台 Top 5
5. 读取 `references/trend-report-template.md`，填充产出报告
6. 保存为 `trend-reports/{date}-daily.md`

## 周五汇总模式

在每日报告基础上额外产出：
- 跨平台共振 TOP 5
- 趋势演变（持续/昙花/上升）
- 本周热门 BGM TOP 5
- Reddit 用户深度关注点
- 与品牌 Content Pillar 的关联建议

读取 `references/trend-summary-template.md`，保存为 `trend-reports/week-{nn}-summary.md`

---

# 模块2：content-planner（每周选题规划）

## 触发时机

每周五，或用户主动请求下周选题。

## 依赖

- 模块1的 `week-{nn}-summary.md`（本周热点汇总）
- `listening-config.md` 中的 Content Pillars
- `about-me.md` + `voice.md`（品牌定位）

## 选题评分框架

| 维度 | 权重 | 说明 |
|------|------|------|
| 热度 | 30% | 本周该话题在各平台的传播力 |
| 品牌&产品相关性 | 35% | 与品牌定位/当月主推产品的关联 |
| Content Pillar 重叠 | 25% | 必须命中至少1个 pillar |
| 可执行性 | 10% | 制作难度、素材可获得性 |

## 执行流程

1. 读取本周 trend-summary
2. 读取 listening-config.md 的 Content Pillars 和当月主推
3. 按评分框架对每个热点话题评分
4. 为下周一~周五安排每日选题，覆盖不同 pillar
5. 每个选题明确：选题名、目标平台、展示形式、对应 Pillar、热度来源、选题理由
6. 提供文案方向提示（hook → body → CTA）
7. 检查 pillar 覆盖均衡性
8. 读取 `references/content-plan-template.md`，保存为 `content-plans/week-{nn}-plan.md`

---

# 模块3：content-creator（品牌内容制作）

## 3.0 brand-voice-trainer（品牌调性训练）

> 所有内容制作子技能的前置依赖。brand-voice.md 不存在时自动跳转此技能。

### 执行流程

1. 向用户索取品牌过往社媒内容（最少10条，建议20条，覆盖不同平台和内容类型）
2. 收集方式三选一：A.用户粘贴文本 B.Apify抓取品牌主页 C.上传CSV
3. 多维度分析样本：
   - 语气与性格（3-5关键词 + 温度/正式度/自信度 1-10）
   - 文案特征（平均句长/段落节奏/钩子类型/CTA风格/标志用语）
   - 视觉风格（主色/排版/字体/调性）
   - 视频风格（时长偏好/节奏/出镜方式/BGM偏好）
   - 禁区识别（absence signals：从未出现的用词/结构/语气）
   - 平台差异化（同品牌在不同平台的语气差异）
4. 产出 `brand-voice.md`，读取 `references/brand-voice-template.md` 模板
5. 回测验证：用规则重写3条样本，匹配度≥80%则通过

### 核心产出
`brand-voice.md`，包含：品牌性格、语气参数、文案规则(要做/不做)、钩子偏好、CTA偏好、标志用语、平台差异化表、视觉规范、视频规范、品牌禁区。

## 3.1 copy-writer（文案撰写）

### 前置检查
1. 读取 brand-voice.md，不存在→跳转 brand-voice-trainer
2. 读取本周 content-plan（如有）
3. 读取 listening-config.md（content pillars）

### 执行流程

1. **确定选题&平台**：从 content-plan 提取 / 用户指定 / 用户粘贴素材
2. **选择框架**（按内容类型匹配）：

| 内容类型 | 框架 | 结构 |
|---------|------|------|
| 痛点切入 | PAS | Pain→Agitate→Solve |
| 产品推广 | AIDA | Attention→Interest→Desire→Action |
| 场景对比 | BAB | Before→After→Bridge |
| 用户故事 | STAR | Situation→Task→Action→Result |
| 观点输出 | SLAY | Statement→List→Application→You |
| 教程干货 | How-to | 问题→步骤→总结 |
| 种草安利 | PDR | Problem→Demo→Result |

3. **撰写草稿**，严格执行 brand-voice.md 规则：
   - 语气/正式度/自信度 → 对应用词句式
   - 钩子 → 使用偏好排序前3的类型
   - CTA → 使用指定风格
   - 禁区 → 逐条检查，违反则重写
   - 平台差异化 → 按目标平台调整

4. **各平台长度硬约束**：

| 平台 | 推荐长度 | Hashtag数 | 首行规则 |
|------|---------|----------|---------|
| IG | ≤150词 | 5-7 | 不看more也能读 |
| TikTok | ≤80词 | 3-5 | 前2s决定留存 |
| X | ≤280字符 | 1-2 | 全文可见 |
| LinkedIn | ≤1,300字符 | 3-5 | 钩子+空行 |
| YouTube | ≤200词描述 | 标签区 | 标题即钩子 |
| Facebook | ≤250词 | 3-5 | 钩子 |

5. **自检**：品牌调性匹配/钩子强度/CTA明确/长度合规/禁区触碰
6. 保存为 `drafts/{date}-{topic}-{platform}.md`

## 3.2 graphic-maker（图文制作）

### 前置检查
1. 读取 brand-voice.md（视觉规范部分）
2. 如有 brand-kit.md，优先读取
3. 读取关联文案草稿

### 内容类型判断

| 内容特征 | 推荐类型 | 适配平台 |
|---------|---------|---------|
| 数据/对比/流程/框架 | 信息图 Infographic | IG Carousel / LinkedIn |
| 观点/清单/步骤/教程 | 轮播图 Carousel | IG / LinkedIn / Facebook |
| 金句/预告/公告/种草 | 单图 Single Post | IG / X / Facebook |
| 产品展示/新功能 | 产品图 Product Shot | 全平台 |

### 平台尺寸硬约束

读取 `references/platform-specs.md` 获取完整尺寸表。核心规格：

| 类型 | 平台 | 尺寸(px) | 比例 |
|------|------|----------|------|
| 方形帖 | IG/LinkedIn/FB | 1080×1080 | 1:1 |
| 竖版帖 | IG | 1080×1350 | 4:5 |
| Stories/Reels封面 | IG/FB | 1080×1920 | 9:16 |
| 横版帖 | X/LinkedIn | 1200×675 | 16:9 |
| Carousel | IG/LinkedIn | 1080×1350 | 4:5 |
| YouTube缩略图 | YouTube | 1280×720 | 16:9 |
| TikTok封面 | TikTok | 1080×1920 | 9:16 |

### 生成方式（三选一）

**方式A：image_generate 直出（推荐）**
构建 prompt：[平台标识] + 品牌视觉关键词 + 内容类型 + 尺寸 + 品牌色 + 文字内容(双引号) + 排版要求。调用 image_generate 工具直接生成图片。

**方式B：Gemini Prompt 输出**
适用白板手绘风/复杂信息图。输出完整 Gemini image generation prompt，用户复制到 Gemini chat 的 Create Image 模式。

**方式C：Canva 设计规范**
适用需人工微调。输出 Canva 可导入的设计指令文档（元素清单+文字内容+导出设置）。

### Carousel 多页规范
- 逐页生成，风格参数一致
- 封面页 + 内容页 + CTA 页，视觉区分
- 每页 body 文字 ≤15 词
- 保存到 `assets/{date}-{topic}-{platform}/`

## 3.3 video-scripter（视频脚本+制作）

### 前置检查
1. 读取 brand-voice.md（文案规则 + 视频规范）
2. 读取关联文案草稿 / content-plan 选题
3. 如有参考爆款链接，进入「爆款拆解」模式

### 视频类型

| 类型 | 时长 | 适配平台 |
|------|------|---------|
| 短Reel | ≤15s | TikTok/IG Reel |
| 标准Reel | 30s | TikTok/IG Reel/YouTube Shorts |
| 深Reel | 60s | TikTok/IG Reel/YouTube Shorts |
| 长视频 | 3-10min | YouTube |

### 爆款拆解模式
1. 抓取参考视频数据
2. 分析结构：钩子→冲突→高潮→CTA
3. 提取可借鉴元素（钩子类型/节奏/BGM/画面切换）
4. 按 brand-voice.md 重写：保留结构骨架，替换品牌语气

### 脚本模板
分镜表：时间 | 画面 | 旁白/字幕 | 音乐/BGM | 备注

### 全局规则
- 前2s必须有强钩子
- 旁白语气匹配 brand-voice.md
- 每5-7s一个节奏变化点
- CTA在最后3s
- 竖版：1080×1920, 9:16 | 横版：1920×1080, 16:9

### 生成方式
- 方式A：create_project(sub_type=2) AI视频生成
- 方式B：graphic-maker生成分镜图 + 拍摄指南
- 方式C：纯脚本文档交付

## 3.4 post-formatter（格式适配 & 发布就绪）

### 前置检查
1. 读取 brand-voice.md
2. 读取待发布文案草稿
3. 读取关联图片/视频素材

### 各平台排版规范

读取 `references/platform-specs.md` 获取完整规则。核心要点：

- **IG**：钩子不看more可读，空行分段，Hashtag末尾5-7个用"."分隔
- **TikTok**：精简≤80词，字幕必须内嵌，Hashtag 3-5个
- **X**：280字符硬上限，Hashtag 1-2个
- **LinkedIn**：空行分隔每段，钩子加粗≤50字符，Hashtag 3-5个
- **YouTube**：标题≤70字符含关键词，描述前150词放核心信息，时间戳(≥3min)
- **Facebook**：≤250词推荐，Hashtag 3-5个

### 发布前终检清单

1. **品牌调性**：语气一致/无禁区内容/CTA符合规范
2. **内容质量**：钩子有效/CTA明确/无错别字敏感词
3. **平台合规**：长度/Hashtag数/图片尺寸/视频格式
4. **内容一致性**：与content-plan一致/命中Content Pillar/多平台核心信息一致/图文匹配
5. **素材检查**：图片视频已生成/格式正确/大小合规

### 产出
为每个平台产出 `publish-ready/{date}-{topic}-{platform}.md`，含：排版后文案(可直接复制)、素材路径、终检结果、建议发布时间。

---

## 凭证说明

| 变量 | 用途 | 所需模块 |
|------|------|---------|
| APIFY_API_TOKEN | 各平台数据抓取 | trend-radar / brand-voice-trainer / video-scripter |
| GOOGLE_AI_API_KEY | Gemini 图片生成 | graphic-maker |

无 API Token 时，trend-radar 降级为搜索工具获取热门内容，其他模块正常使用。
