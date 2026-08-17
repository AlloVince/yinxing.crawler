# DMM 列表搜索参数说明

本文记录 DMM AV 列表页使用的 GraphQL 搜索参数，重点说明哪些参数会改变结果集，以及如何利用筛选参数拆分列表任务。

接口地址：`https://api.video.dmm.co.jp/graphql`

列表查询的 GraphQL operation 为 `AvSearch`，实际数据由 `legacySearchPPV` 返回。

## 1. 参数分类

### 1.1 影响结果集的参数

| 参数 | 作用 | 全量分片建议 |
| --- | --- | --- |
| `floor` | 内容楼层，AV 列表使用 `AV` | 固定，不作为分片维度 |
| `sort` | 排序方式，例如 `RECOMMENDED`、`SALES_RANK_SCORE` | 固定，不作为分片维度 |
| `queryWord` | 关键词搜索 | 不建议作为全量分片，无法证明覆盖完整结果 |
| `filter` | 分类、制作商、演员等筛选条件 | 主要分片手段 |
| `excludeUndelivered` | 是否排除未配信内容 | 应固定，避免不同任务范围不一致 |
| `includeExplicit` | 是否包含显式内容 | 当前固定为 `true` |

`limit` 和 `offset` 只负责分页，不能解决单个查询的总条数或 offset 上限问题。

### 1.2 只控制响应内容的参数

以下变量主要控制 facet、关联词、登录态和附加字段，不会扩大影片结果集：

```text
hasFacet
facetLimit
hasGenreDescription
legacyProductType
hasLegacyProductType
isLoggedIn
shouldFetchGenreRelatedWords
shouldFetchDirectorRelatedWords
shouldFetchLabelRelatedWords
shouldFetchSeriesRelatedWords
shouldFetchActressRelatedWords
shouldFetchMakerRelatedWords
shouldFetchHistrionRelatedWords
shouldGetBookmark
isListUiAbTestTarget
shouldFetchFanzaClipCount
guestToken
```

Spider 只需要内容 ID 时，可以关闭不必要的响应字段，例如：

```json
{
  "hasFacet": false,
  "shouldGetBookmark": false,
  "isLoggedIn": false,
  "shouldFetchFanzaClipCount": false
}
```

不要将登录会话、追踪 Cookie 或 token 写入代码、日志和文档。

## 2. `filter` 筛选结构

`filter` 的类型为 `ContentSearchPPVFilterInput`。当前列表请求中可见的字段如下：

| 字段 | 含义 | 作为主分片的建议 |
| --- | --- | --- |
| `genreIds` | 类型 | 推荐 |
| `makerIds` | 制作商 | 推荐 |
| `labelIds` | 厂牌 | 推荐 |
| `seriesIds` | 系列 | 推荐 |
| `actressIds` | 演员 | 可用，但任务数可能较多 |
| `directorIds` | 导演 | 可用 |
| `histrionIds` | 男演员/出演者 | 可用 |
| `authorIds` | 作者 | 可用 |
| `contentTagIds` | 内容标签 | 可用 |
| `saleIds` | 销售活动 | 不适合覆盖全量 |
| `pointRewardCampaignIds` | 积分活动 | 不适合覆盖全量 |
| `isSaleItemsOnly` | 仅返回促销商品 | 不是全量分片维度 |

ID 类型字段的格式为：

```json
{
  "genreIds": {
    "ids": [{"id": "4025"}],
    "op": "AND"
  }
}
```

### 2.1 `op` 的含义

- 单个 ID 时，`AND` 没有额外影响。
- 多个 ID 使用 `AND` 时，通常表示结果必须同时满足这些条件，结果集会缩小。
- 如果服务端支持 `OR`，可用于合并同一维度的多个 ID；但为了控制单次查询规模，分片任务通常每个只放一个分类 ID。

示例：

```json
{
  "floor": "AV",
  "sort": "SALES_RANK_SCORE",
  "filter": {
    "makerIds": {
      "ids": [{"id": "45276"}],
      "op": "AND"
    }
  },
  "limit": 120,
  "offset": 0
}
```

## 3. facet 与可发现的分片值

当 `hasFacet` 为 `true` 时，列表结果可以返回 facet。当前查询中的 facet 包括：

```text
floor
actress
maker
label
series
genreAndCampaignCombined
```

每个 facet item 通常包含：

```json
{
  "id": "xxx",
  "name": "...",
  "count": 123
}
```

因此可以先执行一次 facet 查询，动态获得以下分片值：

- genre ID；
- maker ID；
- label ID；
- series ID；
- 部分 actress ID。

当前 facet 结构没有直接返回以下维度的完整 ID 列表：

```text
director
histrion
author
contentTag
```

虽然这些字段存在于 `ContentSearchPPVFilterInput`，但在没有其他发现接口时，不应假定可以自动枚举全部值。

## 4. 全量列表与演员分片

此前 spider 使用单一列表查询和 offset 链：

```graphql
legacySearchPPV(
  limit: $limit
  offset: $offset
  floor: AV
  sort: SALES_RANK_SCORE
  facetLimit: 1
  includeExplicit: true
  excludeUndelivered: true
)
```

该查询没有使用 `filter`。因此所有内容都依赖同一个 offset 分页链；即使 `pageInfo.totalCount` 返回 40W+，服务端仍可能对单个查询的可访问 offset 设置上限，最终只能取得约 5W 条。

继续增大 `offset` 或 `limit` 不一定能突破该限制。

当前实现改为先遍历演员目录，再为每个演员创建独立的 `actressIds` 列表查询。演员目录接口和五十音参数见 [`dmm-actress-directory.md`](dmm-actress-directory.md)。

## 5. 推荐的分片策略

第一阶段建议依次使用以下维度建立独立列表任务：

```text
genre → maker → label → series
```

建议流程：

1. 请求默认列表并获取 facet。
2. 收集 genre、maker、label、series 的 ID。
3. 为每个 ID 创建独立搜索任务。
4. 每个任务使用自己的 `filter` 和 `offset` 分页。
5. 所有详情请求按内容 ID 去重。

不同维度之间会产生重复。例如，同一影片可能同时属于某个 genre、maker 和 label。因此不能直接累加各分片的数量，必须依靠 Scrapy 请求去重或内容 ID 去重。

演员维度可以作为第二阶段补充。演员数量通常较多，热门演员的结果也可能超过单任务限制，不宜一开始就把全部演员拆成任务。

## 6. 推荐的查询改造方向

最小改动方式是保留现有详情查询，只改造列表部分：

1. 将列表查询补充为支持 `$filter` 的 `AvSearch` 结构。
2. 将 `filter` 放入列表请求的 `variables`。
3. 增加 facet 查询，动态发现分片 ID。
4. 将筛选条件编码到列表请求中。
5. 分页时沿用同一个筛选条件。
6. 通过内容 ID 去重详情请求。

建议记录每个分片的以下信息，便于确认是否仍受到站点限制：

```text
分片类型
分片 ID
pageInfo.totalCount
最终 offset
返回内容数量
去重后的内容数量
```

## 7. FANZA Spider 抓取模式

当前 Spider 根据 `APP_RUN_DEEP` 分为两种模式：

### 普通抓取

默认不设置 `APP_RUN_DEEP` 或设置为 `0`：

```text
sort = DATE
filter = null
limit = 120
最大页数 = 10
```

普通模式只请求列表前 10 页，offset 为 `0、120、240 ... 1080`，最多取得 1200 个内容 ID，再进入现有详情请求流程。

### 深度抓取

设置：

```bash
APP_RUN_DEEP=1 uv run scrapy crawl fanza
```

深度模式包含两类入口，均走「入口 → 列表分页到底 → 详情」：

1. 遍历 47 个五十音演员目录，为每个演员创建 `actressIds` 列表任务；
2. 遍历分类页 `/av/list` 的 genre 列表（硬编码 282 个去重 ID），为每个 genre 创建 `genreIds` 列表任务。

演员与类别是平行的分片维度，单个列表请求只携带 `actressIds` 或 `genreIds` 之一，不会同时出现。两类列表任务排序保持为 `SALES_RANK_SCORE`，均分页到底。
