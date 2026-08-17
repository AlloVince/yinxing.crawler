# DMM 详情页 GraphQL 请求归并说明

## 目的

本文根据详情页实际产生的 11 个 GraphQL 请求整理字段、用途和归并方案，供后续讨论 DMM Spider 的采集范围与请求设计使用。

请求地址：`https://api.video.dmm.co.jp/graphql`

本文只记录 GraphQL 请求结构，不保存浏览器登录 Cookie。当前接口关闭 introspection，字段清单来自详情页实际请求和响应验证，不能视为完整服务端 schema。

## 结论摘要

详情页请求可以按数据所有权归并为三组：

1. **核心原始数据**：`ContentPageData` + `UserReviews`。这是 Spider 最应该落盘的主体。
2. **页面公共数据**：`Root`、`Maintenance`、`PromotionBanners`、`SideBar`。它们与具体影片无关，适合独立缓存或按需请求。
3. **个性化/推荐数据**：`RecentlyViewedContents`、`U2iRecommendData`、`ActressInformation`、`BookmarkDiscountCount`。依赖 Cookie、用户状态或页面行为，不建议默认写入影片原始数据。（`I2iRecommendData` 基于当前影片、不依赖登录，已合并进核心详情请求。）

如果只为保存影片原始数据，推荐将 `ppvContent`、`reviewSummary` 和 `reviews` 合并为一个请求；其余请求保持可选。

## 请求清单

| Operation | 主要用途 | 是否绑定影片 | 是否依赖登录/行为 | 建议 |
| --- | --- | --- | --- | --- |
| `ContentPageData` | 影片详情、价格、演员、标签、评价汇总 | 是 | 部分字段 | 核心采集 |
| `UserReviews` | 评价明细分页 | 是 | 通常否 | 核心采集，可分页 |
| `RecentlyViewedContents` | 最近浏览影片摘要 | 否，多 ID | 浏览 Cookie | 可选 |
| `I2iRecommendData` | 基于当前影片的相似推荐 | 是 | 否 | 已合并进详情请求 |
| `U2iRecommendData` | 面向用户的推荐 | 否 | 是 | 默认跳过 |
| `ActressInformation` | 按演员查询关联影片 | 否，多演员 | 否 | 可选，成本较高 |
| `SideBar` | 销售、积分、演员/标签/系列排行、品牌店 | 否 | 页面参数 | 默认跳过 |
| `PromotionBanners` | 详情页广告/优惠横幅 | 否 | 页面参数 | 默认跳过 |
| `BookmarkDiscountCount` | 用户收藏和演员收藏中的折扣数量 | 否 | 是 | 默认跳过 |
| `Root` | IP 国家与访问状态 | 否 | IP | 运行环境信息 |
| `Maintenance` | PPV 服务维护窗口 | 否 | 否 | 请求失败排障辅助 |

## 核心详情请求

### `ContentPageData`

请求根字段：

```graphql
ppvContent(id: $id) { ...ContentData }
reviewSummary(contentId: $id) { ...ReviewSummary }
```

### `ReviewSummary`

| 字段 | 用途 |
| --- | --- |
| `average` | 平均评价分数 |
| `total` | 评价总数 |
| `withCommentTotal` | 带文字内容的评价数量 |
| `distributions.total` | 对应星级的评价数量 |
| `distributions.withCommentTotal` | 对应星级中带文字评价数量 |
| `distributions.rating` | 星级，通常为 1～5 |

### `ContentData`：基本信息

| 字段 | 用途 |
| --- | --- |
| `id` | 内容 ID/影片编号 |
| `floor` | 内容所属楼层/业务分类 |
| `title` | 标题 |
| `contentType` | 内容类型，例如普通 AV、VR 等 |
| `isExclusiveDelivery` | 是否独家配信 |
| `releaseStatus` | 发布/配信状态 |
| `description` | 影片描述 |
| `notices` | 页面提示或注意事项 |
| `isNoIndex` | 是否禁止搜索引擎索引 |
| `isAllowForeign` | 是否允许海外访问 |
| `isInWishList` | 当前用户是否已收藏；需登录态变量 |
| `announcements.body` | 影片相关公告 |
| `featureArticles.link` | 关联特辑文章的 URL、文案 |

### 图片与样片

| 字段 | 用途 |
| --- | --- |
| `packageImage.largeUrl` / `mediumUrl` | 封面图 |
| `sampleImages.number` | 样片序号 |
| `sampleImages.imageUrl` / `largeImageUrl` | 样片图片 |
| `mostPopularContentImage` | 页面主推图片，可能是样片或封面联合类型 |
| `sample2DMovie.highestMovieUrl` | 2D 样片最高质量地址 |
| `sample2DMovie.hlsMovieUrl` | 2D HLS 样片地址 |
| `sampleVRMovie.highestMovieUrl` | VR 样片最高质量地址 |

### 价格与促销

| 字段 | 用途 |
| --- | --- |
| `pricing.lowestEffectivePriceInclusiveTax` | 当前最低有效含税价格 |
| `pricing.lowestRegularPriceInclusiveTax` | 当前最低原价含税价格 |
| `pricing.sale` | 折扣活动名称、ID、结束时间 |
| `pricing.pointRewardCampaign` | 积分活动名称、ID、结束时间、活动 ID、倍率 |
| `products` | 具体商品/配信单元列表 |
| `products.id` / `priority` | 商品标识与排序 |
| `deliveryUnit` | 配信单元及流媒体/下载质量组 |
| `regularPriceInclusiveTax` / `effectivePriceInclusiveTax` | 商品原价与有效价格 |
| `expireDays` | 商品有效期 |
| `licenseType` | 授权类型 |
| `shopName` | 店铺名称 |
| `couponDiscount` | 优惠券及折后价格；部分字段依赖登录态 |

### 分类与人员

| 字段 | 用途 |
| --- | --- |
| `actresses` | 演员 ID、名称、假名、头像及部分统计 |
| `histrions` | 男演员/出演者 |
| `directors` | 导演 |
| `authors` | 影视类作者 |
| `maker` | 制作商 |
| `label` | 厂牌 |
| `series` | 系列 |
| `genres` | 类型标签 |
| `makerContentId` | 制作商侧编号 |
| `actresses.ppvSummary.contentCount` | 演员在 AV 楼层的内容数量 |
| `isFavorite` / `isBookmarked` | 当前用户对演员的收藏状态 |
| `relatedTags` | 相关标签或标签组 |

### 排名与播放能力

| 字段 | 用途 |
| --- | --- |
| `weeklyRanking` | 周榜排名 |
| `monthlyRanking` | 月榜排名 |
| `playableInfo` | 播放设备、设备组、质量能力 |
| `isStreamable` | 是否可流式播放 |
| `isDownloadable` | 是否可下载 |
| `isSupported` | 设备是否支持 |
| `vrViewingType` | VR 观看类型 |

## 评价明细：`UserReviews`

```graphql
reviews(contentId: $id, sort: $sort, limit: 10, offset: $offset) {
  items { ... }
}
```

| 字段 | 用途 |
| --- | --- |
| `id` | 评价 ID |
| `title` | 评价标题 |
| `rating` | 单条评价星级 |
| `reviewerId` | 评价者 ID |
| `nickname` | 评价者昵称 |
| `isPurchased` | 是否购买过 |
| `comment` | 评价正文 |
| `helpfulCount` | 评价被标记有帮助的次数 |
| `service` | 评价来源服务 |
| `isExposure` | 是否允许展示 |
| `publishDate` | 发布时间 |

当前请求使用 `HELPFUL_COUNT_DESC`，每页 10 条。`offset` 可用于继续抓取后续评价。

## 推荐与摘要请求

### `RecentlyViewedContents`

批量接收最近浏览的内容 ID，返回 `PPVContentSummary`：

- `id`、`title`、`floor`、`contentType`
- `packageImage.smallUrl` / `mediumUrl`
- `releaseStatus`、`isExclusiveDelivery`、`wishlistCount`
- `pricing` 下的促销、价格、商品价格、积分活动
- `review.average`、`review.total`

### `I2iRecommendData`

根据当前影片返回相似推荐（item-to-item，不依赖登录）。该字段已合并进核心详情请求 `ContentWithReviews` 的 `ppvContent` 选择集，用于从推荐继续扩展抓取推荐影片。

```graphql
query I2iRecommendData($contentId: ID!, $i2iRecommendId: ID!) {
  ppvContent(id: $contentId) {
    ...i2iRecommendedContents
    __typename
  }
}
fragment i2iRecommendedContents on PPVContent {
  recommendedContents(limit: 40, recommendId: $i2iRecommendId) {
    id
    content { ... }
    trackingId
    __typename
  }
}
```

变量示例：

```json
{"contentId": "1piyo00234", "i2iRecommendId": "81b5e821"}
```

- `recommendedContents`：`PPVContent` 上的字段，参数 `limit` 与 `recommendId`。
- `limit`：服务端返回硬上限为 40，大于 40 仍只返回 40 条。
- `recommendId`：即变量 `$i2iRecommendId`，为全局稳定的推荐引擎 ID（当前值 `81b5e821`）；无效 ID 返回 0 条不报错。
- `recommendedContents.id`：推荐影片 ID，用于生成新的详情请求。
- `content`：推荐影片摘要（标题、类型、独家状态、发布状态、封面、收藏数、价格、评价摘要）。
- `trackingId`：推荐链路追踪标识。

### `U2iRecommendData`

仅对登录用户请求。返回用户推荐影片及 `trackingId`，内容摘要字段与 `RecentlyViewedContents` 基本一致。该数据与影片本身无关，建议不进入影片原始记录。

### `ActressInformation`

对每位演员单独执行 `legacySearchPPV`，查询其关联影片。每个结果包含：

- `id`、`title`、`packageImage.mediumUrl`
- `releaseStatus`、`isExclusiveDelivery`
- `salesInfo`：最低价格、多价格标志、活动名称/折扣/结束时间、积分活动
- `review.average`、`review.count`
- `contentType`、`bookmarkCount`
- `pageInfo.hasNext`

该请求会按演员数量放大请求数，不建议与核心详情请求默认合并。

## 页面公共请求

### `SideBar`

- `ppvSales`：销售活动 ID 与名称
- `ppvPointRewardCampaigns`：积分活动或活动组 ID 与名称
- `ppvActressRanking`：月度演员排行
- `ppvLabelRanking`：月度厂牌排行
- `ppvSeriesRanking`：月度系列排行
- `brandStores`：品牌店 ID 与名称

排行、品牌店和活动信息是页面导航数据，不属于单影片实体。

### `PromotionBanners`

返回弹窗、页头或浮动广告：

- `id`、`promotionId`、`promotionName`
- `imageUrl`、`destinationUrl`、`altText`
- `priority`、`backgroundColor`
- `acquiredCoupon.expirationAt`、`isExpired`

### `Root` 与 `Maintenance`

- `Root.ipInfo.countryCode`：访问来源国家
- `Root.ipInfo.accessStatus`：访问状态
- `Maintenance.maintenance.description`：维护说明
- `startAt` / `endAt`：维护时间窗口

这两类字段适合用于运行诊断，不建议写入每条影片数据。

### `BookmarkDiscountCount`

登录用户收藏相关的折扣统计：

- `wishList.discountCount`：收藏影片中的折扣数量
- `favoriteActressList.discountCount`：收藏演员关联内容中的折扣数量

## 推荐的合并请求

Spider 的核心请求可以合并为一个 operation：

```graphql
query ContentRawData($id: ID!, $sort: ReviewSort!, $offset: Int!) {
  ppvContent(id: $id) {
    # ContentData 的核心字段
    id
    floor
    title
    description
    contentType
    releaseStatus
    isExclusiveDelivery
    packageImage { largeUrl mediumUrl }
    sampleImages { number imageUrl largeImageUrl }
    wishlistCount
    maker { id name }
    label { id name }
    series { id name }
    genres { id name }
    actresses { id name nameRuby imageUrl }
    directors { id name }
    relatedTags(limit: 16) { __typename }
  }
  reviewSummary(contentId: $id) {
    average
    total
    withCommentTotal
    distributions { total withCommentTotal rating }
  }
  reviews(contentId: $id, sort: $sort, limit: 10, offset: $offset) {
    items {
      id title rating reviewerId nickname isPurchased comment
      helpfulCount service isExposure publishDate
    }
  }
}
```

实际实现时应根据是否需要价格、样片、播放能力和登录态字段扩展 `ppvContent`，并保留完整 GraphQL 原始响应。`reviewSummary` 与 `reviews` 可以在同一请求中共存；评价明细后续通过 `offset` 单独分页即可。

## 采集边界建议

### 默认采集

- `ppvContent` 核心详情（含 `recommendedContents` 相似推荐）
- `reviewSummary`
- `reviews` 第一页
- 原始请求变量和抓取时间

### 可配置采集

- 后续评价页
- `RecentlyViewedContents`
- `ActressInformation`

### 默认不采集

- `U2iRecommendData`
- `BookmarkDiscountCount`
- `SideBar`
- `PromotionBanners`
- `Root`
- `Maintenance`

原因是这些字段多数是页面公共信息、用户个性化信息或运行环境信息，会增加请求量并污染影片实体数据。
