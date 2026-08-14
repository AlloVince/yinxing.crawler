# DMM GraphQL 原始数据接口

本文档记录当前 DMM Spider 使用的公开 GraphQL 接口、查询字段和原始落盘结构。

Spider 只负责抓取和保存原始 GraphQL 响应，不将字段改名、转换或映射为旧版 ES 文档。旧版字段兼容属于下游 ETL 责任。

## 1. 接口概览

| 项目 | 内容 |
| --- | --- |
| 列表入口 | `https://video.dmm.co.jp/av/list/` |
| GraphQL | `https://api.video.dmm.co.jp/graphql` |
| 详情页 | `https://video.dmm.co.jp/av/content/?id={content_id}` |
| 年龄确认 | Cookie `age_check_done=1` |
| 列表查询 | `legacySearchPPV` |
| 详情查询 | `ppvContent` + `reviews` |
| 评论排序 | `HELPFUL_COUNT_DESC` |
| 评论范围 | 仅第一页，`limit=10`、`offset=0` |

请求至少使用：

```http
Content-Type: application/json
Origin: https://video.dmm.co.jp
Referer: https://video.dmm.co.jp/av/list/
Cookie: age_check_done=1
```

不要把登录会话、追踪 Cookie 或密钥写入代码、日志和文档。

## 2. 列表查询

```graphql
query AvContentIds($limit: Int!, $offset: Int!) {
  legacySearchPPV(
    limit: $limit
    offset: $offset
    floor: AV
    sort: SALES_RANK_SCORE
    facetLimit: 1
    includeExplicit: true
    excludeUndelivered: true
  ) {
    result {
      contents { id }
      pageInfo { totalCount }
    }
  }
}
```

变量：

```json
{"limit": 120, "offset": 0}
```

响应重点：

```json
{
  "data": {
    "legacySearchPPV": {
      "result": {
        "contents": [{"id": "snos00233"}],
        "pageInfo": {"totalCount": 475902}
      }
    }
  }
}
```

Spider 使用 `offset + 当前页数量` 继续分页，直到 `offset >= totalCount` 或接口返回空页。

## 3. 详情与评论合并查询

```graphql
query ContentWithReviews($id: ID!, $sort: ReviewSort!) {
  ppvContent(id: $id) {
    id
    title
    description
    contentType
    releaseStatus
    isExclusiveDelivery
    wishlistCount
    duration
    saleStartDate
    saleEndDate
    deliveryStartDate
    packageImage {
      mediumUrl
      largeUrl
      smallUrl
    }
    sampleImages { imageUrl }
    pricing {
      lowestRegularPriceInclusiveTax
      lowestEffectivePriceInclusiveTax
      hasMultiplePrices
    }
    actresses { id name imageUrl }
    genres { id name }
    maker { id name }
    series { id name }
    label { id name }
    directors { id name }
    relatedTags(limit: 100) {
      __typename
      ... on ContentTag { id name }
    }
  }
  reviews(contentId: $id, sort: $sort, limit: 10, offset: 0) {
    items {
      id
      title
      rating
      reviewerId
      nickname
      isPurchased
      comment
      helpfulCount
      service
      isExposure
      publishDate
      __typename
    }
  }
}
```

变量：

```json
{"id": "hublk00067", "sort": "HELPFUL_COUNT_DESC"}
```

一次请求同时返回影片主体和评论第一页。评论接口虽然支持 `offset`，当前 Spider 按需求只请求 `offset=0`，不抓取后续评论页。

## 4. `ppvContent` 字段说明

| 字段 | 类型/含义 |
| --- | --- |
| `id` | DMM 内容 ID，例如 `hublk00067` |
| `title` | 影片标题 |
| `description` | 影片简介 |
| `contentType` | 内容类型，例如 `TWO_DIMENSION` |
| `releaseStatus` | 发布状态，例如 `SEMI_NEW_RELEASE` |
| `isExclusiveDelivery` | 是否独家配信 |
| `wishlistCount` | 收藏数 |
| `duration` | 时长，接口原始整数；不要在 Spider 中转换单位 |
| `saleStartDate` | 销售开始时间，ISO 8601 |
| `saleEndDate` | 销售结束时间，可能为 `null` |
| `deliveryStartDate` | 配信开始时间，ISO 8601 |
| `packageImage` | 封面图 URL，包含中/大/小图 |
| `sampleImages` | 样片截图 URL 列表 |
| `pricing` | 原价、当前有效价格、多价格标记 |
| `actresses` | 演员 ID、姓名、头像 URL |
| `genres` | 类型 ID 和名称 |
| `maker` | 制作商 ID 和名称 |
| `series` | 系列 ID 和名称 |
| `label` | 标签/厂牌 ID 和名称 |
| `directors` | 导演 ID 和名称 |
| `relatedTags` | 关联标签；GraphQL union 中非 `ContentTag` 类型可能只有 `__typename` |

## 5. `reviews.items` 字段说明

| 字段 | 含义 |
| --- | --- |
| `id` | 评论 ID |
| `title` | 评论标题 |
| `rating` | 评论评分 |
| `reviewerId` | 评论用户 ID |
| `nickname` | 评论昵称 |
| `isPurchased` | 是否购买/租赁用户 |
| `comment` | 评论正文 |
| `helpfulCount` | 有帮助计数 |
| `service` | 来源服务，例如 `VIDEO`、`MONO` |
| `isExposure` | 是否曝光/展示标记 |
| `publishDate` | 评论发布时间，ISO 8601 |
| `__typename` | GraphQL 类型名 |

## 6. 原始落盘结构

`RawJsonItem` 的外层包含 EvaScrapy 通用元数据；`content` 内保存 GraphQL 原始响应，不做 ETL：

```json
{
  "url": "https://video.dmm.co.jp/av/content/?id=hublk00067",
  "version": "2.0.0",
  "task": "...",
  "timestamp": 0,
  "content": {
    "data": {
      "ppvContent": {},
      "reviews": {"items": []}
    }
  }
}
```

如果 GraphQL 返回 `errors`，Spider 不落盘该详情 Item，而是让 Scrapy 的失败/重试机制处理，避免将部分详情误判为完整数据。

## 7. 限速与调试

在 EvaScrapy 根目录的 `.env` 设置：

```env
DOWNLOAD_DELAY=2
CONCURRENT_REQUESTS_PER_DOMAIN=1
AUTOTHROTTLE_ENABLED=true
```

验证实际生效值：

```bash
uv run scrapy settings --get DOWNLOAD_DELAY
uv run scrapy settings --get CONCURRENT_REQUESTS_PER_DOMAIN
uv run scrapy settings --get AUTOTHROTTLE_ENABLED
```

启动：

```bash
uv run scrapy crawl dmm
```
